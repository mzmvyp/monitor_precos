"""Gerenciador de alertas de preço por email."""
from __future__ import annotations

import logging
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import pandas as pd
import yaml

LOGGER = logging.getLogger(__name__)


class AlertManager:
    """Gerencia alertas de preço por email."""
    
    def __init__(
        self,
        config_path: Path = Path("config/alerts.yaml"),
        alert_history_path: Path = Path("data/alert_history.csv"),
    ):
        self.config_path = config_path
        self.alert_history_path = alert_history_path
        self.config = self._load_config()
        self._ensure_history_file()
    
    def _load_config(self) -> dict:
        """Carrega configuração de alertas."""
        if not self.config_path.exists():
            LOGGER.warning(f"Arquivo de configuração não encontrado: {self.config_path}")
            return {"email": {"enabled": False}}
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    def _ensure_history_file(self) -> None:
        """Garante que o arquivo de histórico existe."""
        if not self.alert_history_path.parent.exists():
            self.alert_history_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.alert_history_path.exists():
            df = pd.DataFrame(columns=[
                "timestamp",
                "product_id",
                "product_name",
                "store",
                "current_price",
                "previous_price",
                "reduction_percent",
                "alert_sent",
            ])
            df.to_csv(self.alert_history_path, index=False, encoding="utf-8")
    
    def _can_send_alert(self, product_id: str, store: str) -> bool:
        """Verifica se pode enviar alerta (cooldown)."""
        if not self.alert_history_path.exists():
            return True
        
        df = pd.read_csv(self.alert_history_path, encoding="utf-8")
        if df.empty:
            return True
        
        # Filtrar alertas deste produto/loja
        product_alerts = df[
            (df["product_id"] == product_id) &
            (df["store"] == store) &
            (df["alert_sent"] == True)
        ]
        
        if product_alerts.empty:
            return True
        
        # Verificar último alerta
        last_alert = pd.to_datetime(product_alerts["timestamp"].iloc[-1], utc=True)
        cooldown_hours = self.config.get("alerts", {}).get("cooldown_hours", 6)
        cooldown = timedelta(hours=cooldown_hours)
        
        return datetime.now(timezone.utc) - last_alert > cooldown
    
    def _send_email(
        self,
        subject: str,
        body: str,
        recipient: Optional[str] = None
    ) -> bool:
        """Envia email de alerta."""
        email_config = self.config.get("email", {})
        
        if not email_config.get("enabled", False):
            LOGGER.info("Alertas por email desabilitados")
            return False
        
        sender = email_config.get("sender_email")
        password = email_config.get("sender_password")
        recipient = recipient or email_config.get("recipient")
        
        if not all([sender, password, recipient]):
            LOGGER.warning("Configuração de email incompleta. Configure em config/alerts.yaml")
            return False
        
        try:
            # Criar mensagem
            msg = MIMEMultipart()
            msg["From"] = sender
            msg["To"] = recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))
            
            # Enviar via SMTP
            smtp_server = email_config.get("smtp_server", "smtp.gmail.com")
            smtp_port = email_config.get("smtp_port", 587)
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender, password)
                server.send_message(msg)
            
            LOGGER.info(f"✅ Email enviado para {recipient}")
            return True
            
        except Exception as e:
            LOGGER.error(f"❌ Erro ao enviar email: {e}")
            return False
    
    def check_and_alert(
        self,
        product_id: str,
        product_name: str,
        store: str,
        url: str,
        current_price: float,
        previous_price: Optional[float],
        desired_price: Optional[float] = None,
    ) -> bool:
        """
        Verifica se deve enviar alerta e envia se necessário.
        
        Returns:
            True se alerta foi enviado, False caso contrário
        """
        # Verificar thresholds
        alerts_config = self.config.get("alerts", {})
        priority_products = alerts_config.get("priority_products", [])
        
        is_priority = product_id in priority_products
        threshold = (
            alerts_config.get("priority_threshold", 2.0)
            if is_priority
            else alerts_config.get("price_drop_threshold", 5.0)
        )
        
        # VALIDAÇÃO CRÍTICA: Verificar se o preço atual não é suspeito antes de qualquer alerta
        # Detectar preços muito baixos que podem ser erros de scraping
        if previous_price:
            reduction_percent = ((previous_price - current_price) / previous_price) * 100
            # Se redução > 80% e preço anterior era razoável (< 10k), provavelmente é erro
            if reduction_percent > 80 and previous_price < 10000 and current_price < 500:
                LOGGER.warning(
                    f"⚠️ PREÇO SUSPEITO DETECTADO - Não enviando alerta: {product_name} "
                    f"Preço atual: R$ {current_price:.2f} (anterior: R$ {previous_price:.2f}, "
                    f"redução: {reduction_percent:.1f}%). Provável erro de scraping."
                )
                return False
        
        # Verificar se deve alertar
        should_alert = False
        reduction_percent = 0.0
        
        # 1. Abaixo do preço desejado (PRIORIDADE - sempre alerta, mesmo sem redução)
        if (
            alerts_config.get("below_desired_price", True) and
            desired_price and
            current_price <= desired_price
        ):
            # VALIDAÇÃO: Se o preço desejado é muito maior que o atual, pode ser erro
            if desired_price > current_price * 5 and current_price < 500:
                LOGGER.warning(
                    f"⚠️ PREÇO ABAIXO DO DESEJADO MAS SUSPEITO - Não enviando alerta: {product_name} "
                    f"Preço atual: R$ {current_price:.2f} (desejado: R$ {desired_price:.2f}). "
                    f"Diferença muito grande, provável erro de scraping."
                )
                return False
            
            should_alert = True
            # Calcular redução para exibir no email
            if previous_price:
                reduction_percent = ((previous_price - current_price) / previous_price) * 100
            else:
                reduction_percent = 0.0
            LOGGER.info(f"🎯 Preço abaixo do desejado: {product_name} - R$ {current_price:.2f} <= R$ {desired_price:.2f}")
        
        # 2. Redução percentual (só se não estiver abaixo do desired_price)
        elif previous_price and current_price < previous_price:
            reduction_percent = ((previous_price - current_price) / previous_price) * 100
            if reduction_percent >= threshold:
                should_alert = True
                LOGGER.info(f"📉 Redução detectada: {product_name} - {reduction_percent:.1f}% (threshold: {threshold}%)")
        
        if not should_alert:
            return False
        
        # Verificar cooldown
        if not self._can_send_alert(product_id, store):
            LOGGER.info(f"⏳ Cooldown ativo para {product_name} ({store})")
            return False
        
        # Preparar mensagem
        messages_config = self.config.get("messages", {})
        subject_template = messages_config.get(
            "subject_template",
            "🔥 ALERTA DE PREÇO: {product_name}"
        )
        body_template = messages_config.get(
            "body_template",
            "Produto: {product_name}\nPreço: R$ {current_price}\nRedução: {reduction_percent}%"
        )
        
        subject = subject_template.format(product_name=product_name)
        brasilia_now = datetime.now(ZoneInfo("America/Sao_Paulo"))
        
        # Formatar valores para o template
        previous_price_str = f"{previous_price:.2f}" if previous_price else "N/A"
        reduction_percent_str = f"{reduction_percent:.1f}%" if previous_price else "N/A"
        desired_price_str = f"{desired_price:.2f}" if desired_price else "N/A"
        
        body = body_template.format(
            product_name=product_name,
            store=store.upper(),
            current_price=f"{current_price:.2f}",
            previous_price=previous_price_str,
            reduction_percent=reduction_percent_str,
            desired_price=desired_price_str,
            url=url,
            timestamp=brasilia_now.strftime("%d/%m/%Y %H:%M:%S"),
        )
        
        # Enviar email
        alert_sent = self._send_email(subject, body)
        
        # Registrar no histórico
        self._log_alert(
            product_id=product_id,
            product_name=product_name,
            store=store,
            current_price=current_price,
            previous_price=previous_price,
            reduction_percent=reduction_percent,
            alert_sent=alert_sent,
        )
        
        return alert_sent
    
    def _log_alert(
        self,
        product_id: str,
        product_name: str,
        store: str,
        current_price: float,
        previous_price: float,
        reduction_percent: float,
        alert_sent: bool,
    ) -> None:
        """Registra alerta no histórico."""
        new_row = pd.DataFrame([{
            "timestamp": datetime.now(timezone.utc),
            "product_id": product_id,
            "product_name": product_name,
            "store": store,
            "current_price": current_price,
            "previous_price": previous_price,
            "reduction_percent": reduction_percent,
            "alert_sent": alert_sent,
        }])

        if self.alert_history_path.exists():
            df = pd.read_csv(self.alert_history_path, encoding="utf-8")
            df = pd.concat([df, new_row], ignore_index=True)
        else:
            df = new_row

        df.to_csv(self.alert_history_path, index=False, encoding="utf-8")

    def alert_open_box(
        self,
        product_id: str,
        product_name: str,
        store: str,
        product_url: str,
        open_box_url: str,
        regular_price: float,
        open_box_price: Optional[float] = None,
    ) -> bool:
        """
        Envia alerta quando detecta Open Box disponível.

        Returns:
            True se alerta foi enviado, False caso contrário
        """
        # Verificar cooldown para Open Box (usar store + "-openbox" como identificador único)
        open_box_id = f"{product_id}-openbox"
        if not self._can_send_alert(open_box_id, store):
            LOGGER.info(f"⏳ Cooldown ativo para Open Box: {product_name} ({store})")
            return False

        # Preparar mensagem de Open Box
        subject = f"📦 OPEN BOX DISPONÍVEL: {product_name}"

        # Calcular economia se temos o preço do Open Box
        economy_text = ""
        if open_box_price:
            economy = regular_price - open_box_price
            economy_percent = (economy / regular_price) * 100
            economy_text = f"""
💰 PREÇO NORMAL: R$ {regular_price:.2f}
📦 PREÇO OPEN BOX: R$ {open_box_price:.2f}
💵 ECONOMIA: R$ {economy:.2f} ({economy_percent:.1f}%)
"""

        brasilia_now = datetime.now(ZoneInfo("America/Sao_Paulo"))
        body = f"""🎯 OPEN BOX DETECTADO!

Produto: {product_name}
Loja: {store.upper()}
{economy_text}
ℹ️ Open Box = Produto com caixa aberta, devolução ou mostruário
   Funciona perfeitamente, mas pode ter sinais de uso

🔗 VER OPEN BOX:
{open_box_url}

🔗 PRODUTO NORMAL:
{product_url}

⏰ Alerta enviado em: {brasilia_now.strftime("%d/%m/%Y %H:%M:%S")}

---
Monitor de Preços Automático
Aproveite essa oportunidade! 📦✨
"""

        # Enviar email
        alert_sent = self._send_email(subject, body)

        # Registrar no histórico (usando formato especial para Open Box)
        self._log_alert(
            product_id=open_box_id,
            product_name=f"{product_name} (Open Box)",
            store=store,
            current_price=open_box_price or 0.0,
            previous_price=regular_price,
            reduction_percent=((regular_price - open_box_price) / regular_price * 100) if open_box_price else 0.0,
            alert_sent=alert_sent,
        )

        return alert_sent


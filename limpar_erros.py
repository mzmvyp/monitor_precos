"""Script para limpar registros com erro de SSL do histórico."""
import pandas as pd
from pathlib import Path

history_file = Path("data/price_history.csv")

if not history_file.exists():
    print("Arquivo de histórico não encontrado!")
    exit(1)

# Ler histórico
df = pd.read_csv(history_file)

print(f"Total de registros: {len(df)}")
print(f"Registros com erro: {df['error'].notna().sum()}")
print(f"Registros OK: {df['error'].isna().sum()}")

# Remover registros com erro de SSL
df_clean = df[~df['error'].str.contains('CERTIFICATE_VERIFY_FAILED', na=False)]

print(f"\nApós limpeza:")
print(f"Total de registros: {len(df_clean)}")
print(f"Registros removidos: {len(df) - len(df_clean)}")

# Salvar backup
backup_file = history_file.with_suffix('.csv.backup')
df.to_csv(backup_file, index=False)
print(f"\nBackup salvo em: {backup_file}")

# Salvar arquivo limpo
df_clean.to_csv(history_file, index=False)
print(f"Histórico limpo salvo em: {history_file}")
print("\n✅ Pronto! Recarregue o dashboard (F5)")



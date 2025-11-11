# 📋 Produtos Monitorados

## Processadores (CPU)

### Processador AMD Ryzen 5 9600X
- **Preço Desejado**: R$ 1.500,00
- **Lojas**: KaBuM, Amazon
- **Alternativas**: Ryzen 7 7700, 7700X, 5 7600X

### Processador AMD Ryzen 7 7700
- **Preço Desejado**: R$ 1.400,00
- **Lojas**: Terabyte, Pichau

### Processador AMD Ryzen 7 7700X
- **Preço Desejado**: R$ 1.500,00
- **Lojas**: Pichau

### Processador AMD Ryzen 5 7600X
- **Preço Desejado**: R$ 1.100,00
- **Lojas**: Pichau

---

## Placa-Mãe

### Placa-Mãe ASUS TUF Gaming B650M-E WiFi
- **Preço Desejado**: R$ 1.400,00
- **Lojas**: KaBuM, Amazon, Terabyte

---

## Armazenamento (SSD)

### SSD Kingston KC3000 1TB
- **Preço Desejado**: R$ 850,00
- **Lojas**: KaBuM, Amazon

---

## Memória RAM

### Memória XPG Lancer RGB 32GB (2x16GB) DDR5 6000 CL30
- **Preço Desejado**: R$ 950,00
- **Lojas**: KaBuM

### Memória Kingston Fury Beast EXPO 32GB (2x16GB) DDR5 6000 CL30
- **Preço Desejado**: R$ 900,00
- **Lojas**: KaBuM, Terabyte

---

## Refrigeração (Cooler)

### Water Cooler Rise Mode Aura Ice Black 240mm
- **Preço Desejado**: R$ 450,00
- **Lojas**: KaBuM

### Kit 3 Fans Rise Mode Aura Pro Black
- **Preço Desejado**: R$ 200,00
- **Lojas**: KaBuM

---

## Gabinete (Case)

### Gabinete Kalkan Midgard Mid Tower
- **Preço Desejado**: R$ 250,00
- **Lojas**: KaBuM

---

## Fonte de Alimentação (PSU)

### Fonte Husky Sledger 850W 80 Plus Gold
- **Preço Desejado**: R$ 550,00
- **Lojas**: KaBuM, Amazon

---

## 📊 Estatísticas

- **Total de Produtos**: 11
- **Total de URLs Monitoradas**: 20+
- **Lojas**: KaBuM (10), Amazon (5), Terabyte (4), Pichau (4)
- **Orçamento Total Desejado**: ~R$ 9.000,00

---

## 🎯 Melhores Ofertas Atuais (última coleta)

Confira o dashboard em **http://localhost:8501** para ver os preços em tempo real!

---

## ✏️ Como Adicionar Novos Produtos

Edite o arquivo `config/products.yaml`:

```yaml
- id: "novo-produto"
  name: "Nome do Produto"
  category: "categoria"
  desired_price: 999.0
  urls:
    - store: "kabum"
      url: "https://www.kabum.com.br/produto/..."
    - store: "amazon"
      url: "https://www.amazon.com.br/..."
```

Categorias disponíveis: `cpu`, `motherboard`, `memory`, `storage`, `cooler`, `case`, `psu`, `peripheral`


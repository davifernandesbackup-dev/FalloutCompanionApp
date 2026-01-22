# Wasteland Assistant

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.34%2B-ff4b4b)

**Wasteland Assistant** is a work-in-progress companion application for *XP to Level 3's Fallout Homebrew TTRPG 2.1*, designed to simplify encounter generation, creature management, and character sheets.

> **Disclaimer:** This program was developed with the assistance of AI coding tools. It may contain errors, bugs, or code patterns that do not meet professional software engineering standards.

## 🚀 Features

- **☢️ Encounter Scanner:** Generate random encounters based on biomes, difficulty, and luck.
- **📖 Bestiary:** Browse and search a list of creatures from the Fallout universe, with quick access to their statblocks.
- **📝 Character Sheet:** Create and manage characters with automatic calculation of derived stats (S.P.E.C.I.A.L.).
- **🗃️ Encounter Logs:** Save generated encounters for future reference.
- **🛠️ Database Editor:** Easily add, edit, and remove threats and loot items.

## 🛠️ Installation and Execution

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Run the application:**
    ```bash
    streamlit run main.py
    ```

## 📂 Project Structure

```text
FalloutApp/
├── main.py                 # Application entry point
├── constants.py            # File path definitions
├── requirements.txt        # Project dependencies
├── data/                   # JSON Database (Bestiary, Encounters, Loot, Saves)
├── tabs/                   # Main UI Modules
│   ├── bestiary.py         # Bestiary Viewer
│   ├── charactersheet.py   # Character Sheet
│   ├── utilities.py        # Utilities Tab
│   ├── database_editor.py  # Database Editor Controller
│   ├── character_logic.py  # Character Logic
│   ├── character_components.py # Character UI Components
│   └── encounters/         # Encounters Module (Package)
│       ├── scanner.py      # Encounter Generator
│       └── logs.py         # Save History
│   └── database/           # Database Editor Modules
│       ├── encounters.py   # Threats/Loot Editor
│       ├── items.py        # Equipment/Perks Editor
│       ├── bestiary.py     # Creature Editor
│       └── characters.py   # Character Editor
└── utils/                  # Shared utility functions
    ├── data_manager.py     # JSON Loading/Saving
    ├── dice.py             # Dice rolling logic
    ├── range.py            # Distance converter
    └── special.py          # Modifier calculator
```

---

## 🇧🇷 Português

O **Wasteland Assistant** é uma aplicação (ainda em desenvolvimento) auxiliar para o *XP to Level 3's Fallout Homebrew TTRPG 2.1*, projetada para simplificar a geração de encontros, gestão de criaturas e fichas de personagens.

> **Aviso:** Este programa foi desenvolvido com a assistência de ferramentas de IA. Pode conter erros, bugs ou padrões de código que não atendem aos padrões profissionais de engenharia de software.

### 🚀 Funcionalidades

- **☢️ Scanner de Encontros:** Gere encontros aleatórios com base em biomas, dificuldade e sorte.
- **📖 Bestiário:** Navegue e pesquise uma lista de criaturas do universo Fallout, com acesso rápido aos seus statblocks.
- **📝 Ficha de Personagem:** Crie e gerencie personagens com cálculo automático de stats derivados (S.P.E.C.I.A.L.).
- **🗃️ Registos de Encontros:** Guarde os encontros gerados para referência futura.
- **🛠️ Editor de Base de Dados:** Adicione, edite e remova facilmente ameaças e itens de saque.

### 🛠️ Instalação e Execução

1.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Execute a aplicação:**
    ```bash
    streamlit run main.py
    ```

### 📂 Estrutura do Projeto

```text
FalloutApp/
├── main.py                 # Ponto de entrada da aplicação
├── constants.py            # Definições de caminhos de ficheiros
├── requirements.txt        # Dependências do projeto
├── data/                   # Base de dados JSON (Bestiário, Encontros, Loot, Saves)
├── tabs/                   # Módulos de UI principais
│   ├── bestiary.py         # Visualizador do Bestiário
│   ├── charactersheet.py   # Ficha de Personagem
│   ├── utilities.py        # Tab de Utilitários
│   ├── database_editor.py  # Controlador do Editor de BD
│   ├── character_logic.py  # Lógica da Ficha de Personagem
│   ├── character_components.py # Componentes de UI da Ficha
│   └── encounters/         # Módulo de Encontros (Package)
│       ├── scanner.py      # Gerador de Encontros
│       └── logs.py         # Histórico de Saves
│   └── database/           # Módulos do Editor de BD
│       ├── encounters.py   # Editor de Ameaças/Loot
│       ├── items.py        # Editor de Equipamentos/Perks
│       ├── bestiary.py     # Editor de Criaturas
│       └── characters.py   # Editor de Personagens
└── utils/                  # Funções utilitárias partilhadas
    ├── data_manager.py     # Carregamento/Salvamento de JSON
    ├── dice.py             # Lógica de rolagem de dados
    ├── range.py            # Conversor de distâncias
    └── special.py          # Calculadora de modificadores
```

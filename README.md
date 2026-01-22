# Wasteland Assistant

O Wasteland Assistant é uma aplicação auxiliar para o RPG de mesa Fallout da 2d20 System, projetada para simplificar a geração de encontros e a gestão de criaturas.

## 🚀 Funcionalidades

- **Scanner de Encontros:** Gere encontros aleatórios com base em biomas, dificuldade e sorte.
- **Bestiário:** Navegue e pesquise uma lista de criaturas do universo Fallout, com acesso rápido aos seus statblocks.
- **Registos de Encontros:** Guarde os encontros gerados para referência futura, com funcionalidades de pesquisa e ordenação.
- **Editor de Base de Dados:** Adicione, edite e remova facilmente ameaças e itens de saque da base de dados da aplicação.

## 🛠️ Como Executar a Aplicação

1.  **Instale as dependências:**
    ```bash
    pip install streamlit
    ```
2.  **Execute a aplicação:**
    ```bash
    streamlit run main.py
    ```

## 📂 Estrutura do Projeto

- **`main.py`:** O ponto de entrada da aplicação.
- **`tabs/`:** Contém os módulos para cada separador da aplicação.
  - **`encounters.py`:** A lógica para o scanner de encontros, registos guardados e editor da base de dados.
  - **`bestiary.py`:** A lógica para o bestiário de criaturas.
  - **`utilities.py`:** Um placeholder para futuras ferramentas e utilitários.
- **`data/`:** Contém os ficheiros JSON que alimentam a aplicação.
  - **`bestiary.json`:** A base de dados de criaturas e os seus statblocks.
  - **`encounters.json`:** A base de dados de ameaças para cada bioma.
  - **`loot.json`:** A base de dados de itens de saque para cada bioma.
  - **`saved_encounters.json`:** Onde os encontros guardados são armazenados.
- **`요약.md`:** Um resumo das alterações e melhorias feitas na aplicação.
- **`README.md`:** Este ficheiro.

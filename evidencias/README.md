# Evidências de Execução no SQL Fiddle (MySQL 5.6)

Salve nesta pasta (`evidencias/`) **4 capturas de tela em tela inteira** (usando a tecla `Print Screen` ou a Ferramenta de Captura no modo **Tela Inteira**, sem recortar a janela).

## Requisitos obrigatórios de TODAS as capturas

Cada imagem deve mostrar claramente, ao mesmo tempo:
1. A **barra de endereços** do navegador com `http://sqlfiddle.com/` (ou `https://sqlfiddle.com/`);
2. O SGBD **MySQL 5.6** selecionado na barra superior do SQL Fiddle;
3. O código SQL digitado e o **resultado real da execução** abaixo;
4. A **barra de tarefas** do Windows, incluindo **data e horário** do sistema operacional no canto inferior direito.

---

## Arquivos esperados nesta pasta

| Nº | Nome exato do arquivo | O que executar antes de tirar o print |
|---|---|---|
| 1 | `01_ddl_dml_schema.png` | Cole todo o conteúdo de `sql/sqlfiddle_01_schema_ddl_dml.sql` no painel **esquerdo** (*Schema*), clique em **Build Schema**, cole a consulta de **VERIFICAÇÃO INICIAL** de `sql/sqlfiddle_02_consultas_join.sql` no painel **direito** e clique em **Run SQL**. |
| 2 | `02_consulta1_join_vendas.png` | Com o schema construído, cole apenas a **CONSULTA 1** no painel **direito** e clique em **Run SQL** (deve exibir as 10 vendas ordenadas de 1 a 10). |
| 3 | `03_consulta2_left_join_clientes.png` | Cole apenas a **CONSULTA 2** no painel **direito** e clique em **Run SQL** (deve exibir as 11 linhas, incluindo `Rian` com `codigo_compra` igual a `(null)`). |
| 4 | `04_consulta3_join_antes_data_atual.png` | Cole apenas a **CONSULTA 3** no painel **direito** e clique em **Run SQL** (deve exibir os 3 clientes únicos que compraram antes da data atual: `Caio`, `Marcos` e `Penelope`). |

> **Importante:** Após salvar os 4 arquivos aqui e informar os dados institucionais (Instituição, Curso, Nome completo, Cidade/UF e Orientador(a)), o relatório ABNT final (`.docx` e `.pdf`) será gerado automaticamente com essas imagens incorporadas.

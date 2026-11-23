-- ============================================================================
-- Script DQL para o painel DIREITO ("Run SQL") do SQL Fiddle (MySQL 5.6)
-- Execute UM bloco por vez clicando em "Run SQL" e capture a tela inteira.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- VERIFICACAO INICIAL (para o Print 1: 01_ddl_dml_schema.png)
-- Apos clicar em "Build Schema" no painel esquerdo, execute esta consulta
-- para comprovar a carga correta das 3 tabelas:
-- ----------------------------------------------------------------------------
SELECT 'CLIENTE' AS tabela, COUNT(*) AS total_registros FROM CLIENTE
UNION ALL
SELECT 'PRODUTO', COUNT(*) FROM PRODUTO
UNION ALL
SELECT 'COMPRA', COUNT(*) FROM COMPRA;


-- ----------------------------------------------------------------------------
-- CONSULTA 1 (para o Print 2: 02_consulta1_join_vendas.png)
-- Retornar o numero da venda, nome do cliente, nome do produto e valor da
-- compra, ordenando a saida pelo numero da compra.
-- ----------------------------------------------------------------------------
SELECT
    co.numero AS numero_venda,
    cl.nome AS nome_cliente,
    pr.nome AS nome_produto,
    co.valor_compra
FROM COMPRA co
INNER JOIN CLIENTE cl ON co.codigo_cliente = cl.codigo
INNER JOIN PRODUTO pr ON co.id_produto = pr.id
ORDER BY co.numero ASC;


-- ----------------------------------------------------------------------------
-- CONSULTA 2 (para o Print 3: 03_consulta2_left_join_clientes.png)
-- Demonstrar o nome do(s) cliente(s) e o codigo da compra (exibindo NULL
-- para os clientes que nao compraram na loja).
-- ----------------------------------------------------------------------------
SELECT
    cl.nome AS nome_cliente,
    co.numero AS codigo_compra
FROM CLIENTE cl
LEFT JOIN COMPRA co ON cl.codigo = co.codigo_cliente
ORDER BY cl.codigo ASC, co.numero ASC;


-- ----------------------------------------------------------------------------
-- CONSULTA 3 (para o Print 4: 04_consulta3_join_antes_data_atual.png)
-- Retornar o nome do cliente (sem repeticao) e o telefone dos clientes que
-- tenham comprado na loja antes da data atual.
-- ----------------------------------------------------------------------------
SELECT DISTINCT
    cl.nome AS nome_cliente,
    cl.telefone
FROM CLIENTE cl
INNER JOIN COMPRA co ON cl.codigo = co.codigo_cliente
WHERE co.data_compra < CURRENT_DATE
ORDER BY cl.nome ASC;

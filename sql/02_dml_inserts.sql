-- ============================================================================
-- Disciplina: Gerenciamento e Desenvolvimento em Banco de Dados
-- Banco de Dados: LOJABD
-- SGBD Alvo: MySQL 5.6
-- Etapa 2: Inserção de Dados nas Tabelas (DML)
-- ============================================================================

USE LOJABD;

-- Inserção dos 7 clientes (autoincremento gera códigos de 1 a 7)
INSERT INTO CLIENTE (nome, estado, cidade, telefone) VALUES
    ('Fagner', 'SP', 'P. Prudente', '997989491'),
    ('Maria', 'SP', 'Campinas', '997989493'),
    ('Marcela', 'RJ', 'Angra dos Reis', '997989492'),
    ('Caio', 'SP', 'Assis', '997989495'),
    ('Marcos', 'SP', 'Campos do Jordão', '997989498'),
    ('Penelope', 'MG', 'Itajubá', '997989494'),
    ('Rian', 'SP', 'Santos', '997989490');

-- Inserção dos 4 produtos (autoincremento gera IDs de 1 a 4)
INSERT INTO PRODUTO (nome, valor, quantidade_estoque) VALUES
    ('Mouse', 200.00, 30),
    ('Teclado', 250.00, 15),
    ('Notebook', 3500.00, 10),
    ('Fone de ouvido', 150.00, 25);

-- Inserção das 10 compras
-- Observação: utiliza-se aritmética de datas padrão MySQL (CURRENT_DATE() +/- INTERVAL N DAY)
-- e valor_compra = quantidade_comprada * PRODUTO.valor.
INSERT INTO COMPRA (numero, data_compra, codigo_cliente, id_produto, quantidade_comprada, valor_compra) VALUES
    (1,  CURRENT_DATE(),                   1, 4, 1,  150.00),
    (2,  CURRENT_DATE() + INTERVAL 2 DAY,  2, 2, 2,  500.00),
    (3,  CURRENT_DATE() + INTERVAL 3 DAY,  3, 1, 2,  400.00),
    (4,  CURRENT_DATE() + INTERVAL 1 DAY,  4, 3, 1, 3500.00),
    (5,  CURRENT_DATE() - INTERVAL 2 DAY,  5, 1, 2,  400.00),
    (6,  CURRENT_DATE() - INTERVAL 5 DAY,  6, 3, 1, 3500.00),
    (7,  CURRENT_DATE() - INTERVAL 3 DAY,  5, 2, 1,  250.00),
    (8,  CURRENT_DATE() - INTERVAL 1 DAY,  4, 4, 2,  300.00),
    (9,  CURRENT_DATE(),                   3, 4, 3,  450.00),
    (10, CURRENT_DATE() + INTERVAL 1 DAY,  2, 2, 4, 1000.00);

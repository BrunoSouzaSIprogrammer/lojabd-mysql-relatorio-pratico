-- ============================================================================
-- Disciplina: Gerenciamento e Desenvolvimento em Banco de Dados
-- Banco de Dados: LOJABD (Loja Virtual)
-- SGBD Alvo: MySQL 5.6 (execucao local / servidor dedicado)
-- Autor: Bruno Souza
-- ============================================================================

-- 1. Criacao e selecao do banco de dados
CREATE DATABASE IF NOT EXISTS LOJABD
    DEFAULT CHARACTER SET utf8
    DEFAULT COLLATE utf8_general_ci;

USE LOJABD;

-- Limpeza preventiva para reexecucao segura do script
DROP TABLE IF EXISTS COMPRA;
DROP TABLE IF EXISTS PRODUTO;
DROP TABLE IF EXISTS CLIENTE;

-- ============================================================================
-- ETAPA 1: DDL - Criacao das tabelas e restricoes de integridade
-- ============================================================================

CREATE TABLE CLIENTE (
    codigo   INT AUTO_INCREMENT PRIMARY KEY,
    nome     VARCHAR(100) NOT NULL,
    estado   CHAR(2)      NOT NULL,
    cidade   VARCHAR(100) NOT NULL,
    telefone VARCHAR(20)  NOT NULL
) ENGINE=InnoDB;

CREATE TABLE PRODUTO (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    nome               VARCHAR(100)   NOT NULL,
    valor              DECIMAL(10, 2) NOT NULL,
    quantidade_estoque INT            NOT NULL
) ENGINE=InnoDB;

CREATE TABLE COMPRA (
    numero              INT            PRIMARY KEY,
    data_compra         DATE           NOT NULL,
    codigo_cliente      INT            NOT NULL,
    id_produto          INT            NOT NULL,
    quantidade_comprada INT            NOT NULL,
    valor_compra        DECIMAL(10, 2) NOT NULL,
    CONSTRAINT fk_compra_cliente
        FOREIGN KEY (codigo_cliente) REFERENCES CLIENTE (codigo),
    CONSTRAINT fk_compra_produto
        FOREIGN KEY (id_produto) REFERENCES PRODUTO (id)
) ENGINE=InnoDB;

-- ============================================================================
-- ETAPA 2: DML - Insercao dos dados nas tabelas
-- ============================================================================

-- Insercao na tabela CLIENTE (7 registros)
INSERT INTO CLIENTE (nome, estado, cidade, telefone) VALUES
    ('Fagner',   'SP', 'P. Prudente',      '997989491'),
    ('Maria',    'SP', 'Campinas',         '997989493'),
    ('Marcela',  'RJ', 'Angra dos Reis',   '997989492'),
    ('Caio',     'SP', 'Assis',            '997989495'),
    ('Marcos',   'SP', 'Campos do Jordão', '997989498'),
    ('Penelope', 'MG', 'Itajubá',          '997989494'),
    ('Rian',     'SP', 'Santos',           '997989490');

-- Insercao na tabela PRODUTO (4 registros)
INSERT INTO PRODUTO (nome, valor, quantidade_estoque) VALUES
    ('Mouse',          200.00,  30),
    ('Teclado',        250.00,  15),
    ('Notebook',       3500.00, 10),
    ('Fone de ouvido', 150.00,  25);

-- Insercao na tabela COMPRA (10 registros)
-- Nota tecnica MySQL 5.6: utiliza-se DATE_ADD / DATE_SUB com INTERVAL
-- em vez de aritmetica direta (CURRENT_DATE + n), evitando conversao
-- numerica YYYYMMDD incorreta nas viradas de mes.
INSERT INTO COMPRA (numero, data_compra, codigo_cliente, id_produto, quantidade_comprada, valor_compra) VALUES
    (1,  CURRENT_DATE,                           1, 4, 1, 150.00),
    (2,  DATE_ADD(CURRENT_DATE, INTERVAL 2 DAY), 2, 2, 2, 500.00),
    (3,  DATE_ADD(CURRENT_DATE, INTERVAL 3 DAY), 3, 1, 2, 400.00),
    (4,  DATE_ADD(CURRENT_DATE, INTERVAL 1 DAY), 4, 3, 1, 3500.00),
    (5,  DATE_SUB(CURRENT_DATE, INTERVAL 2 DAY), 5, 1, 2, 400.00),
    (6,  DATE_SUB(CURRENT_DATE, INTERVAL 5 DAY), 6, 3, 1, 3500.00),
    (7,  DATE_SUB(CURRENT_DATE, INTERVAL 3 DAY), 5, 2, 1, 250.00),
    (8,  DATE_SUB(CURRENT_DATE, INTERVAL 1 DAY), 4, 4, 2, 300.00),
    (9,  CURRENT_DATE,                           3, 4, 3, 450.00),
    (10, DATE_ADD(CURRENT_DATE, INTERVAL 1 DAY), 2, 2, 4, 1000.00);

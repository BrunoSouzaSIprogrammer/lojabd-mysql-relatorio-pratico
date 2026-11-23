-- ============================================================================
-- Script Consolidado (DDL + DML) para Execução no SQL Fiddle (sqlfiddle.com)
-- SGBD: MySQL | Projeto: LOJABD
-- Observação: Em instâncias MySQL locais, utilize CREATE DATABASE LOJABD e
-- USE LOJABD. No ambiente sandbox do SQL Fiddle, o banco temporário já é
-- provisionado automaticamente (CREATE DATABASE gera ERROR 1044 Access denied).
-- ============================================================================

-- CREATE DATABASE IF NOT EXISTS LOJABD
--     DEFAULT CHARACTER SET utf8
--     DEFAULT COLLATE utf8_general_ci;
-- USE LOJABD;

CREATE TABLE CLIENTE (
    codigo INT NOT NULL AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    estado CHAR(2) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    PRIMARY KEY (codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE PRODUTO (
    id INT NOT NULL AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    valor DECIMAL(10, 2) NOT NULL,
    quantidade_estoque INT NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE COMPRA (
    numero INT NOT NULL,
    data_compra DATE NOT NULL,
    codigo_cliente INT NOT NULL,
    id_produto INT NOT NULL,
    quantidade_comprada INT NOT NULL,
    valor_compra DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (numero),
    CONSTRAINT fk_compra_cliente
        FOREIGN KEY (codigo_cliente) REFERENCES CLIENTE (codigo),
    CONSTRAINT fk_compra_produto
        FOREIGN KEY (id_produto) REFERENCES PRODUTO (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

INSERT INTO CLIENTE (nome, estado, cidade, telefone) VALUES
    ('Fagner', 'SP', 'P. Prudente', '997989491'),
    ('Maria', 'SP', 'Campinas', '997989493'),
    ('Marcela', 'RJ', 'Angra dos Reis', '997989492'),
    ('Caio', 'SP', 'Assis', '997989495'),
    ('Marcos', 'SP', 'Campos do Jordão', '997989498'),
    ('Penelope', 'MG', 'Itajubá', '997989494'),
    ('Rian', 'SP', 'Santos', '997989490');

INSERT INTO PRODUTO (nome, valor, quantidade_estoque) VALUES
    ('Mouse', 200.00, 30),
    ('Teclado', 250.00, 15),
    ('Notebook', 3500.00, 10),
    ('Fone de ouvido', 150.00, 25);

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

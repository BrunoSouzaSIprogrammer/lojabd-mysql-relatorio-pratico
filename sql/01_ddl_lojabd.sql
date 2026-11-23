-- ============================================================================
-- Disciplina: Gerenciamento e Desenvolvimento em Banco de Dados
-- Banco de Dados: LOJABD
-- SGBD Alvo: MySQL 5.6 (compatível com SQL Fiddle e MySQL local)
-- Etapa 1: Criação do Banco de Dados e das Tabelas (DDL)
-- ============================================================================

CREATE DATABASE IF NOT EXISTS LOJABD
    DEFAULT CHARACTER SET utf8
    DEFAULT COLLATE utf8_general_ci;

USE LOJABD;

-- Tabela de Clientes
CREATE TABLE CLIENTE (
    codigo INT NOT NULL AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    estado CHAR(2) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    PRIMARY KEY (codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Tabela de Produtos
CREATE TABLE PRODUTO (
    id INT NOT NULL AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    valor DECIMAL(10, 2) NOT NULL,
    quantidade_estoque INT NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Tabela de Compras (Vendas)
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

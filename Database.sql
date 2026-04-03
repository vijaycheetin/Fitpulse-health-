CREATE DATABASE fit;
USE fit;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50),
    password VARCHAR(255)
);

CREATE TABLE health_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    heart_rate INT,
    steps INT,
    sleep FLOAT,
    timestamp DATETIME,
    status VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

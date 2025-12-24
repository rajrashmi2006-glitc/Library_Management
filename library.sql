CREATE DATABASE library_db;
USE library_db;

CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50),
    usn VARCHAR(20),
    branch VARCHAR(30),
    semester INT,
    phone VARCHAR(15),
    email VARCHAR(50)
);

CREATE TABLE books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    book_name VARCHAR(50),
    subject VARCHAR(30),
    rack INT,
    row_no INT,
    quantity INT
);

CREATE TABLE issued_books (
    issue_id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT,
    student_id INT,
    issue_date DATE,
    return_date DATE
);

-- Initial books (8 books)
INSERT INTO books VALUES
(1,'Operating System Concepts','OS',1,1,1),
(2,'Modern Operating Systems','OS',1,2,1),
(3,'Computer Networks','CN',2,1,1),
(4,'Data Structures and Algorithms','DS',2,2,1),
(5,'Database Management Systems','DB',3,1,1),
(6,'Python Programming','PL',3,2,1),
(7,'Software Engineering','SE',4,1,1),
(8,'Computer Organization and Architecture','COA',4,2,1)
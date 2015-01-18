
DROP TABLE IF EXISTS Client;
DROP TABLE IF EXISTS User;


CREATE TABLE User (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL
) ENGINE=INNODB;

CREATE TABLE Client (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  UUID CHAR(32),
  UserID INT UNSIGNED NOT NULL,
  FOREIGN KEY (UserID) REFERENCES User(id)
) ENGINE=INNODB;

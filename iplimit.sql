CREATE TABLE `Exception` (
  `ExceptionIP` varchar(50) NOT NULL,
  `CreationDate` datetime NOT NULL,
  `ExpirationDate` datetime NOT NULL,
  `Requestor` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`ExceptionIP`),
  KEY (`ExpirationDate`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


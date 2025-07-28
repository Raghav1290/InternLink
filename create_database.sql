CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(20) NOT NULL,
  `password_hash` char(60) BINARY NOT NULL COMMENT 'Bcrypt Password Hash and Salt (60 bytes)',
  `email` varchar(320) NOT NULL COMMENT 'Maximum email address length according to RFC5321 section 4.5.3.1 is 320 characters (64 for local-part, 1 for at sign, 255 for domain)',
  `role` enum('customer','staff','admin') NOT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `username` (`username`)
)
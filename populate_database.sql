INSERT INTO `users` (`username`, `password_hash`, `email`, `role`)
VALUES
	('customer1', '$2b$12$3W3b9AnL6umkIBm6THGHB.yId0/GuR/Gi7R8ZevTwR0xi3o8rrvZa', 'customer1@example.com', 'customer'),
	('customer2', '$2b$12$6KPIL1c77kZpDXzDDRuJV.ielxGNDUIJPkxl0K5JdQoZTMrcIMBym', 'customer2@example.com', 'customer'),
	('staff1', '$2b$12$OKt92QtCTJmhr4wqRMYZH.6lOSBUh0oGKcvaNerR2fQe6L7.ViQ0O', 'staff1@example.com', 'staff'),
	('staff2', '$2b$12$mT8QI2wKBvpoOFZsRwaLkeuS9FS4vc6sX.GJNnNMA1EKmypk6UYGa', 'staff2@example.com', 'staff'),
	('admin1', '$2b$12$.jUTmK8lb/4O8O3oFuHyeerUl9qs1c.slhGzpYDMJqxGnnToGPuMO', 'admin1@example.com', 'admin');
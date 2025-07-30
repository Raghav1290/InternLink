-- Adding this command to ensure that there is no error occuring chances while creating new tables
DROP TABLE IF EXISTS `application`;
DROP TABLE IF EXISTS `internship`;
DROP TABLE IF EXISTS `student`;
DROP TABLE IF EXISTS `employer`;
DROP TABLE IF EXISTS `users`;

-- Creating users table
CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL UNIQUE,
  `full_name` varchar(100) DEFAULT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` char(60) BINARY NOT NULL COMMENT 'Bcrypt Password Hash and Salt (60 bytes)',
  `profile_image` varchar(255) DEFAULT NULL,
  `role` enum('student','employer','admin') NOT NULL,
  `status` enum('active','inactive') NOT NULL DEFAULT 'active',
  PRIMARY KEY (`user_id`)
);

-- Creating student table
CREATE TABLE `student` (
  `student_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL UNIQUE,
  `university` varchar(100) DEFAULT NULL,
  `course` varchar(100) DEFAULT NULL,
  `resume_path` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`student_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Creating employer table
CREATE TABLE `employer` (
  `emp_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL UNIQUE,
  `company_name` varchar(100) DEFAULT NULL,
  `company_description` TEXT DEFAULT NULL,
  `website` varchar(100) DEFAULT NULL,
  `logo_path` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`emp_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Creating internship table
CREATE TABLE `internship` (
  `internship_id` int NOT NULL AUTO_INCREMENT,
  `company_id` int NOT NULL,
  `title` varchar(100) NOT NULL,
  `description` TEXT DEFAULT NULL,
  `location` varchar(100) DEFAULT NULL,
  `duration` varchar(50) DEFAULT NULL,
  `skills_required` TEXT DEFAULT NULL,
  `deadline` DATE NOT NULL,
  `stipend` varchar(50) DEFAULT NULL,
  `number_of_opening` int DEFAULT NULL,
  `additional_req` TEXT DEFAULT NULL,
  PRIMARY KEY (`internship_id`),
  FOREIGN KEY (`company_id`) REFERENCES `employer` (`emp_id`) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Creating application table
CREATE TABLE `application` (
  `student_id` int NOT NULL,
  `internship_id` int NOT NULL,
  `status` enum('Pending','Accepted','Rejected') NOT NULL DEFAULT 'Pending',
  `feedback` TEXT DEFAULT NULL,
  PRIMARY KEY (`student_id`, `internship_id`),
  FOREIGN KEY (`student_id`) REFERENCES `student` (`student_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (`internship_id`) REFERENCES `internship` (`internship_id`) ON DELETE CASCADE ON UPDATE CASCADE
);
-- phpMyAdmin SQL Dump
-- version 4.5.2
-- http://www.phpmyadmin.net
--
-- Host: 127.0.0.1
-- Generation Time: Apr 21, 2016 at 04:10 PM
-- Server version: 5.7.9
-- PHP Version: 5.6.16

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `projects-schema`
--

-- --------------------------------------------------------

--
-- Table structure for table `text_types`
--

DROP TABLE IF EXISTS `text_types`;
CREATE TABLE IF NOT EXISTS `text_types` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `type` varchar(250) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `text_types`
--

INSERT INTO `text_types` (`id`, `type`) VALUES
(1, 'Introduction'),
(2, 'Abstract'),
(3, 'References'),
(4, 'Conslusion'),
(5, 'Future Endevours'),
(6, 'Concept'),
(7, 'Methodologies'),
(8, 'Diagrams'),
(9, 'Contributors'),
(10, 'Topics'),
(11, 'Tools'),
(12, 'Main Points'),
(13, 'Science Fiction References'),
(14, 'Vision'),
(15, 'Motivation'),
(16, 'Main Idea'),
(17, 'Inspiration');

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

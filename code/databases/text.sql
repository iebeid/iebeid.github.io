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
-- Table structure for table `text`
--

DROP TABLE IF EXISTS `text`;
CREATE TABLE IF NOT EXISTS `text` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `text` longtext NOT NULL,
  `text-types_id` int(11) NOT NULL,
  PRIMARY KEY (`id`,`text-types_id`),
  UNIQUE KEY `id_UNIQUE` (`id`),
  KEY `fk_text_text-types1_idx` (`text-types_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;

--
-- Dumping data for table `text`
--

INSERT INTO `text` (`id`, `text`, `text-types_id`) VALUES
(1, 'Image warping and transformation has been used since the invention of VR master to create immersive photo experience, Photo-spheres used by google''s street view is an amazing to take the user to the place that he or she intends to view or visit in the future.\r\nRendering Photo-spheres on head mounted display is no new endevour, but showing these photo-sphere images in 4 sided cave would be a great way of showing the capabilities of CAVE environments.', 1),
(2, 'I was on top of Pinnacle mountain one of the highest peaks in Arkansas when I started taking a panorama picture, I wanted to create a photo-sphere image from the panorama and view on an Oculus rift', 17);

--
-- Constraints for dumped tables
--

--
-- Constraints for table `text`
--
ALTER TABLE `text`
  ADD CONSTRAINT `fk_text_text-types1` FOREIGN KEY (`text-types_id`) REFERENCES `text_types` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema projects
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema projects
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `projects` DEFAULT CHARACTER SET latin1 ;
USE `projects` ;

-- -----------------------------------------------------
-- Table `projects`.`document_types`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects`.`document_types` (
  `id` INT(11) NOT NULL,
  `type` VARCHAR(512) NOT NULL,
  PRIMARY KEY (`id`))
ENGINE = MyISAM
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `projects`.`projects`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects`.`projects` (
  `id` INT(11) NOT NULL,
  `title` TEXT NOT NULL,
  `year` INT(11) NOT NULL,
  `organization` VARCHAR(512) NULL DEFAULT NULL,
  `short_description` TEXT NULL DEFAULT NULL,
  `long_description` TEXT NULL DEFAULT NULL,
  `reference` TEXT NULL DEFAULT NULL,
  `url` VARCHAR(512) NULL DEFAULT NULL,
  PRIMARY KEY (`id`))
ENGINE = MyISAM
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `projects`.`documents`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects`.`documents` (
  `id` INT(11) NOT NULL,
  `url` VARCHAR(512) NOT NULL,
  `document_types_id` INT(11) NOT NULL,
  `projects_id` INT(11) NOT NULL,
  PRIMARY KEY (`id`, `document_types_id`, `projects_id`),
  INDEX `fk_documents_document_types_idx` (`document_types_id` ASC),
  INDEX `fk_documents_projects1_idx` (`projects_id` ASC))
ENGINE = MyISAM
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `projects`.`images`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects`.`images` (
  `id` INT(11) NOT NULL,
  `url` VARCHAR(512) NOT NULL,
  `projects_id` INT(11) NOT NULL,
  PRIMARY KEY (`id`, `projects_id`),
  INDEX `fk_images_projects1_idx` (`projects_id` ASC))
ENGINE = MyISAM
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `projects`.`people`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects`.`people` (
  `id` INT(11) NOT NULL,
  `first_name` VARCHAR(512) NOT NULL,
  `last_name` VARCHAR(512) NOT NULL,
  `website` VARCHAR(512) NOT NULL,
  `projects_id` INT(11) NOT NULL,
  PRIMARY KEY (`id`, `projects_id`),
  INDEX `fk_people_projects1_idx` (`projects_id` ASC))
ENGINE = MyISAM
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `projects`.`source_code`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects`.`source_code` (
  `id` INT(11) NOT NULL,
  `url` VARCHAR(512) NOT NULL,
  `projects_id` INT(11) NOT NULL,
  PRIMARY KEY (`id`, `projects_id`),
  INDEX `fk_source_code_projects1_idx` (`projects_id` ASC))
ENGINE = MyISAM
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `projects`.`videos`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects`.`videos` (
  `id` INT(11) NOT NULL,
  `url` VARCHAR(512) NOT NULL,
  `projects_id` INT(11) NOT NULL,
  PRIMARY KEY (`id`, `projects_id`),
  INDEX `fk_videos_projects1_idx` (`projects_id` ASC))
ENGINE = MyISAM
DEFAULT CHARACTER SET = latin1;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

-- -----------------------------------------------------
-- Schema projects-schema
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema projects-schema
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `projects-schema` DEFAULT CHARACTER SET utf8 ;
USE `projects-schema` ;

-- -----------------------------------------------------
-- Table `projects-schema`.`text_types`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects-schema`.`text_types` (
  `id` INT NOT NULL DEFAULT 1,
  `type` VARCHAR(250) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `projects-schema`.`text`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects-schema`.`text` (
  `id` INT NOT NULL DEFAULT 1,
  `text` LONGTEXT NOT NULL,
  `text-types_id` INT NOT NULL,
  PRIMARY KEY (`id`, `text-types_id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC),
  INDEX `fk_text_text-types1_idx` (`text-types_id` ASC),
  CONSTRAINT `fk_text_text-types1`
    FOREIGN KEY (`text-types_id`)
    REFERENCES `projects-schema`.`text_types` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `projects-schema`.`description`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects-schema`.`description` (
  `id` INT NOT NULL DEFAULT 1,
  `text_id` INT NOT NULL,
  `text_text-types_id` INT NOT NULL,
  PRIMARY KEY (`id`, `text_id`, `text_text-types_id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC),
  INDEX `fk_description_text1_idx` (`text_id` ASC, `text_text-types_id` ASC),
  CONSTRAINT `fk_description_text1`
    FOREIGN KEY (`text_id` , `text_text-types_id`)
    REFERENCES `projects-schema`.`text` (`id` , `text-types_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `projects-schema`.`organization`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects-schema`.`organization` (
  `id` INT NOT NULL DEFAULT 1,
  `name` VARCHAR(250) NOT NULL,
  `address` VARCHAR(250) NOT NULL,
  `department` VARCHAR(250) NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `projects-schema`.`projects`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects-schema`.`projects` (
  `id` INT NOT NULL DEFAULT 1,
  `title` VARCHAR(250) NOT NULL,
  `date` DATE NOT NULL,
  `source_code_link` VARCHAR(250) NULL,
  `current` CHAR NOT NULL,
  `description_id` INT NOT NULL,
  `team` CHAR NOT NULL,
  `organization_id` INT NOT NULL,
  PRIMARY KEY (`id`, `description_id`, `organization_id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC),
  INDEX `fk_projects_description1_idx` (`description_id` ASC),
  INDEX `fk_projects_organization1_idx` (`organization_id` ASC),
  CONSTRAINT `fk_projects_description1`
    FOREIGN KEY (`description_id`)
    REFERENCES `projects-schema`.`description` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_projects_organization1`
    FOREIGN KEY (`organization_id`)
    REFERENCES `projects-schema`.`organization` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `projects-schema`.`people`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects-schema`.`people` (
  `id` INT NOT NULL DEFAULT 1,
  `name` VARCHAR(100) NOT NULL,
  `phone` VARCHAR(45) NULL,
  `email` VARCHAR(45) NULL,
  `role` VARCHAR(45) NULL,
  `organization_id` INT NOT NULL,
  PRIMARY KEY (`id`, `organization_id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC),
  INDEX `fk_people_organization1_idx` (`organization_id` ASC),
  CONSTRAINT `fk_people_organization1`
    FOREIGN KEY (`organization_id`)
    REFERENCES `projects-schema`.`organization` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `projects-schema`.`videos`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects-schema`.`videos` (
  `id` INT NOT NULL DEFAULT 1,
  `title` VARCHAR(45) NOT NULL,
  `description` VARCHAR(250) NULL,
  `link` VARCHAR(250) NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `projects-schema`.`projects_has_videos`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects-schema`.`projects_has_videos` (
  `projects_id` INT NOT NULL,
  `videos_id` INT NOT NULL,
  PRIMARY KEY (`projects_id`, `videos_id`),
  INDEX `fk_projects_has_videos_videos1_idx` (`videos_id` ASC),
  INDEX `fk_projects_has_videos_projects1_idx` (`projects_id` ASC),
  CONSTRAINT `fk_projects_has_videos_projects1`
    FOREIGN KEY (`projects_id`)
    REFERENCES `projects-schema`.`projects` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_projects_has_videos_videos1`
    FOREIGN KEY (`videos_id`)
    REFERENCES `projects-schema`.`videos` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `projects-schema`.`images`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects-schema`.`images` (
  `id` INT NOT NULL DEFAULT 1,
  `name` VARCHAR(250) NOT NULL,
  `caption` VARCHAR(250) NULL,
  `link` VARCHAR(250) NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `projects-schema`.`projects_has_images`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects-schema`.`projects_has_images` (
  `projects_id` INT NOT NULL,
  `images_id` INT NOT NULL,
  PRIMARY KEY (`projects_id`, `images_id`),
  INDEX `fk_projects_has_images_images1_idx` (`images_id` ASC),
  INDEX `fk_projects_has_images_projects1_idx` (`projects_id` ASC),
  CONSTRAINT `fk_projects_has_images_projects1`
    FOREIGN KEY (`projects_id`)
    REFERENCES `projects-schema`.`projects` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_projects_has_images_images1`
    FOREIGN KEY (`images_id`)
    REFERENCES `projects-schema`.`images` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `projects-schema`.`document_types`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects-schema`.`document_types` (
  `id` INT NOT NULL DEFAULT 1,
  `type` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `projects-schema`.`documents`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects-schema`.`documents` (
  `id` INT NOT NULL DEFAULT 1,
  `title` VARCHAR(250) NOT NULL,
  `link` VARCHAR(250) NOT NULL,
  `document_types_id` INT NOT NULL,
  PRIMARY KEY (`id`, `document_types_id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC),
  INDEX `fk_documents_document_types1_idx` (`document_types_id` ASC),
  CONSTRAINT `fk_documents_document_types1`
    FOREIGN KEY (`document_types_id`)
    REFERENCES `projects-schema`.`document_types` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `projects-schema`.`projects_has_documents`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects-schema`.`projects_has_documents` (
  `projects_id` INT NOT NULL,
  `documents_id` INT NOT NULL,
  PRIMARY KEY (`projects_id`, `documents_id`),
  INDEX `fk_projects_has_documents_documents1_idx` (`documents_id` ASC),
  INDEX `fk_projects_has_documents_projects1_idx` (`projects_id` ASC),
  CONSTRAINT `fk_projects_has_documents_projects1`
    FOREIGN KEY (`projects_id`)
    REFERENCES `projects-schema`.`projects` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_projects_has_documents_documents1`
    FOREIGN KEY (`documents_id`)
    REFERENCES `projects-schema`.`documents` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `projects-schema`.`media_types`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects-schema`.`media_types` (
  `id` INT NOT NULL DEFAULT 1,
  `type` VARCHAR(45) NULL,
  `name` VARCHAR(45) NULL,
  `icon` VARCHAR(45) NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `projects-schema`.`projects_has_media_types`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects-schema`.`projects_has_media_types` (
  `projects_id` INT NOT NULL,
  `media_types_id` INT NOT NULL,
  PRIMARY KEY (`projects_id`, `media_types_id`),
  INDEX `fk_projects_has_media_types_media_types1_idx` (`media_types_id` ASC),
  INDEX `fk_projects_has_media_types_projects1_idx` (`projects_id` ASC),
  CONSTRAINT `fk_projects_has_media_types_projects1`
    FOREIGN KEY (`projects_id`)
    REFERENCES `projects-schema`.`projects` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_projects_has_media_types_media_types1`
    FOREIGN KEY (`media_types_id`)
    REFERENCES `projects-schema`.`media_types` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `projects-schema`.`venue`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects-schema`.`venue` (
  `id` INT NOT NULL DEFAULT 1,
  `name` VARCHAR(250) NOT NULL,
  `title` VARCHAR(250) NOT NULL,
  `date` DATE NOT NULL,
  `type` VARCHAR(250) NULL,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `projects-schema`.`projects_has_venue`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `projects-schema`.`projects_has_venue` (
  `projects_id` INT NOT NULL,
  `projects_description_id` INT NOT NULL,
  `projects_organization_id` INT NOT NULL,
  `venue_id` INT NOT NULL,
  PRIMARY KEY (`projects_id`, `projects_description_id`, `projects_organization_id`, `venue_id`),
  INDEX `fk_projects_has_venue_venue1_idx` (`venue_id` ASC),
  INDEX `fk_projects_has_venue_projects1_idx` (`projects_id` ASC, `projects_description_id` ASC, `projects_organization_id` ASC),
  CONSTRAINT `fk_projects_has_venue_projects1`
    FOREIGN KEY (`projects_id` , `projects_description_id` , `projects_organization_id`)
    REFERENCES `projects-schema`.`projects` (`id` , `description_id` , `organization_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_projects_has_venue_venue1`
    FOREIGN KEY (`venue_id`)
    REFERENCES `projects-schema`.`venue` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

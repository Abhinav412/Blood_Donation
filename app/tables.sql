CREATE DATABASE IF NOT EXISTS blood_donation_db;
USE blood_donation_db;

-- Donor Table
CREATE TABLE IF NOT EXISTS Donor (
    donor_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    blood_type VARCHAR(5) NOT NULL,
    last_donation DATE,
    eligibility_status VARCHAR(15)
);

-- Blood Inventory Table
CREATE TABLE IF NOT EXISTS BloodInventory (
    blood_type VARCHAR(5) PRIMARY KEY,
    units_available INT,
    expiration_date DATE,
    is_safe BOOLEAN
);

-- Blood Requests Table
CREATE TABLE IF NOT EXISTS BloodRequests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    requester_type VARCHAR(50),
    blood_type VARCHAR(5),
    quantity INT,
    status VARCHAR(20)
);

-- User Table
CREATE TABLE IF NOT EXISTS User (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    password VARCHAR(50),
    role VARCHAR(20)
);

ALTER TABLE Donor
ADD COLUMN email VARCHAR(255) NOT NULL;
-- Table to store blood banks
CREATE TABLE IF NOT EXISTS BloodBank (
    blood_bank_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    location VARCHAR(255),
    contact_number VARCHAR(15)
);
CREATE TABLE Appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    donor_id INT,
    blood_bank_id INT,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    FOREIGN KEY (donor_id) REFERENCES Donor(donor_id),
    FOREIGN KEY (blood_bank_id) REFERENCES BloodBank(blood_bank_id)
);

DELIMITER //
CREATE PROCEDURE add_blood_bank (
    IN p_name VARCHAR(100),
    IN p_location VARCHAR(255),
    IN p_contact_number VARCHAR(15)
)
BEGIN
    INSERT INTO BloodBank (name, location, contact_number)
    VALUES (p_name, p_location, p_contact_number);
END //
DELIMITER ;
DELIMITER $$

CREATE TRIGGER after_donor_registration
AFTER INSERT ON Donor
FOR EACH ROW
BEGIN
    DECLARE v_blood_type VARCHAR(5);
    
    
    SET v_blood_type = NEW.blood_type;
    
    
    INSERT INTO BloodInventory (blood_type, units_available, blood_bank_id)
    VALUES (v_blood_type, 1, NEW.blood_bank_id)
    ON DUPLICATE KEY UPDATE units_available = units_available + 1;
END$$

DELIMITER ;
DELIMITER //

CREATE PROCEDURE update_blood_inventory(
    IN p_blood_bank_id INT,
    IN p_blood_type VARCHAR(10),
    IN p_units_available INT
)
BEGIN
    INSERT INTO BloodInventory (blood_bank_id, blood_type, units_available)
    VALUES (p_blood_bank_id, p_blood_type, p_units_available)
    ON DUPLICATE KEY UPDATE units_available = p_units_available;
END //

DELIMITER ;


DELIMITER //

CREATE PROCEDURE get_donors_for_blood_bank(p_blood_bank_id INT)
BEGIN
    SELECT 
        d.first_name,
        d.last_name,
        d.email,
        d.blood_type,
        d.last_donation,
        d.eligibility_status
    FROM Donor d
    WHERE d.blood_bank_id = p_blood_bank_id;
END //

DELIMITER ;
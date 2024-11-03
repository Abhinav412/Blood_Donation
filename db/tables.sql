
CREATE DATABASE blood_donation_system;
USE blood_donation_system;


CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    user_type ENUM('donor', 'hospital_staff', 'blood_bank_staff', 'admin') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE donor_profiles (
    donor_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    full_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    blood_type ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NOT NULL,
    contact_number VARCHAR(15) NOT NULL,
    address TEXT NOT NULL,
    last_donation_date DATE,
    medical_history TEXT,
    is_eligible BOOLEAN DEFAULT true,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);


CREATE TABLE blood_banks (
    bank_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    contact_number VARCHAR(15) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL
);


CREATE TABLE blood_inventory (
    inventory_id INT PRIMARY KEY AUTO_INCREMENT,
    bank_id INT,
    blood_type ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NOT NULL,
    units_available INT NOT NULL DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (bank_id) REFERENCES blood_banks(bank_id)
);


CREATE TABLE donation_records (
    donation_id INT PRIMARY KEY AUTO_INCREMENT,
    donor_id INT,
    bank_id INT,
    donation_date DATE NOT NULL,
    blood_type ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NOT NULL,
    units_donated INT NOT NULL,
    quality_test_status ENUM('pending', 'passed', 'failed') DEFAULT 'pending',
    FOREIGN KEY (donor_id) REFERENCES donor_profiles(donor_id),
    FOREIGN KEY (bank_id) REFERENCES blood_banks(bank_id)
);


CREATE TABLE blood_requests (
    request_id INT PRIMARY KEY AUTO_INCREMENT,
    requesting_hospital_id INT,
    blood_type ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NOT NULL,
    units_required INT NOT NULL,
    priority ENUM('low', 'medium', 'high', 'critical') NOT NULL,
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'approved', 'fulfilled', 'cancelled') DEFAULT 'pending',
    FOREIGN KEY (requesting_hospital_id) REFERENCES blood_banks(bank_id)
);


DELIMITER //

-- Trigger to update inventory after donation
CREATE TRIGGER after_donation_insert
AFTER INSERT ON donation_records
FOR EACH ROW
BEGIN
    IF NEW.quality_test_status = 'passed' THEN
        UPDATE blood_inventory
        SET units_available = units_available + NEW.units_donated
        WHERE bank_id = NEW.bank_id AND blood_type = NEW.blood_type;
    END IF;
END//

-- Trigger to update inventory after request fulfillment
CREATE TRIGGER after_request_update
AFTER UPDATE ON blood_requests
FOR EACH ROW
BEGIN
    IF NEW.status = 'fulfilled' AND OLD.status != 'fulfilled' THEN
        UPDATE blood_inventory
        SET units_available = units_available - NEW.units_required
        WHERE bank_id = NEW.requesting_hospital_id 
        AND blood_type = NEW.blood_type;
    END IF;
END//

-- Check donor eligibility
CREATE PROCEDURE check_donor_eligibility(IN donor_id_param INT, OUT is_eligible BOOLEAN)
BEGIN
    DECLARE last_donation DATE;
    SELECT last_donation_date INTO last_donation
    FROM donor_profiles
    WHERE donor_id = donor_id_param;
    
    IF last_donation IS NULL OR DATEDIFF(CURRENT_DATE, last_donation) >= 56 THEN
        SET is_eligible = TRUE;
    ELSE
        SET is_eligible = FALSE;
    END IF;
END//

-- Process blood request
CREATE PROCEDURE process_blood_request(
    IN request_id_param INT,
    IN bank_id_param INT,
    OUT status_message VARCHAR(100)
)
BEGIN
    DECLARE required_units INT;
    DECLARE available_units INT;
    DECLARE required_blood_type VARCHAR(3);
    
    -- Get request details
    SELECT blood_type, units_required
    INTO required_blood_type, required_units
    FROM blood_requests
    WHERE request_id = request_id_param;
    
    -- Check availability
    SELECT units_available INTO available_units
    FROM blood_inventory
    WHERE bank_id = bank_id_param AND blood_type = required_blood_type;
    
    IF available_units >= required_units THEN
        UPDATE blood_requests
        SET status = 'approved'
        WHERE request_id = request_id_param;
        
        SET status_message = 'Request approved';
    ELSE
        SET status_message = 'Insufficient units available';
    END IF;
END//

DELIMITER ;
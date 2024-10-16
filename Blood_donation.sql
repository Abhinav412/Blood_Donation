create database blood_donation;
use blood_donation;

create table donor(
DonorId INT primary key,
DonorName varchar(100),
DOB date,
Gender enum('Male','Female','Other'),
ContactNumber varchar(15)
);

create table blood(
BloodID int primary key,
BloodType varchar(5),
Cost decimal(10,2)
);

create table hospital(
HospitalID int primary key,
HospitalName varchar(100),
Address text,
ContactNumber varchar(15)
);

create table patient(
PatientID int,
HospitalID int,
PatientName varchar(100),
ContactNumber varchar(15),
primary key (PatientID, HospitalID),
foreign key (HospitalID) references hospital(HospitalID)
);

create table bloodbank(
BloodBankID int primary key,
BloodType varchar(5),
Orders int
);

create table users(
UserId int primary key auto_increment,
Username varchar(100) unique,
Password varchar(100),
Role enum('Donor','Admin'),
HospitalID int NULL,
BloodBankID int NULL,
DonorID int NULL,
foreign key(HospitalID) references hospital(HospitalID),
foreign key(DonorID) references donor(DonorID),
foreign key(BloodBankID) references bloodbank(BloodBankID)
);

create table donates(
DonorID int,
BloodID int,
Primary key(DonorID,BloodID),
foreign key (DonorID) references donor(DonorID),
foreign key(BloodID) references blood(BloodID)
);

create table stores(
BloodID int,
BloodBankID int,
primary key(BloodID, BloodBankID),
foreign key (BloodID) references blood(BloodID),
foreign key (BloodBankID) references bloodbank(BloodBankID)
);

create table orders(
BloodBankID int,
HospitalID int,
primary key (BloodBankID, HospitalID),
foreign key (BloodBankID) references bloodbank(BloodBankID),
foreign key (HospitalID) references hospital(HospitalID)
);

create table delivers(
HospitalID int,
PatientID int,
primary key (HospitalID, PatientID),
foreign key (HospitalID) references hospital(HospitalID),
foreign key (PatientID) references patient(PatientID)
);
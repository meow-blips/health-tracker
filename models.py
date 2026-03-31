from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Boolean, Text, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class CyclePhase(str, enum.Enum):
    MENSTRUAL = "menstrual"
    FOLLICULAR = "follicular"
    OVULATORY = "ovulatory"
    LUTEAL = "luteal"


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    full_name = Column(String(200), default="")
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    notify_meds = Column(Boolean, default=True)
    notify_periods = Column(Boolean, default=True)
    notify_water = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    water_logs = relationship("WaterLog", back_populates="user", cascade="all, delete-orphan")
    calorie_logs = relationship("CalorieLog", back_populates="user", cascade="all, delete-orphan")
    exercise_logs = relationship("ExerciseLog", back_populates="user", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="user", cascade="all, delete-orphan")
    med_logs = relationship("MedicationLog", back_populates="user", cascade="all, delete-orphan")
    sleep_logs = relationship("SleepLog", back_populates="user", cascade="all, delete-orphan")
    period_logs = relationship("PeriodLog", back_populates="user", cascade="all, delete-orphan")
    allergies = relationship("Allergy", back_populates="user", cascade="all, delete-orphan")
    mood_logs = relationship("MoodLog", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("GoalSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    weight_logs = relationship("WeightLog", back_populates="user", cascade="all, delete-orphan")

    @property
    def bmi(self):
        if self.height_cm and self.weight_kg and self.height_cm > 0:
            height_m = self.height_cm / 100
            return round(self.weight_kg / (height_m ** 2), 1)
        return None

    @property
    def bmi_category(self):
        bmi = self.bmi
        if bmi is None:
            return "Unknown"
        if bmi < 18.5:
            return "Underweight"
        if bmi < 25:
            return "Healthy"
        if bmi < 30:
            return "Overweight"
        return "Obese"


class WaterLog(Base):
    __tablename__ = "water_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    date = Column(Date, nullable=False)
    glasses = Column(Integer, default=0)
    ml_total = Column(Float, default=0)

    user = relationship("User", back_populates="water_logs")


class CalorieLog(Base):
    __tablename__ = "calorie_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    date = Column(Date, nullable=False)
    meal_type = Column(String(50))
    description = Column(Text)
    calories = Column(Float, default=0)
    protein_g = Column(Float, default=0)
    carbs_g = Column(Float, default=0)
    fat_g = Column(Float, default=0)

    user = relationship("User", back_populates="calorie_logs")


class ExerciseLog(Base):
    __tablename__ = "exercise_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    date = Column(Date, nullable=False)
    exercise_type = Column(String(100))
    duration_min = Column(Float, default=0)
    calories_burned = Column(Float, default=0)
    notes = Column(Text)

    user = relationship("User", back_populates="exercise_logs")


class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    name = Column(String(200), nullable=False)
    dosage = Column(String(100))
    frequency = Column(String(100))
    time_of_day = Column(String(50))
    pills_remaining = Column(Integer, default=0)
    notify_refill_at = Column(Integer, default=5)
    active = Column(Boolean, default=True)

    user = relationship("User", back_populates="medications")


class MedicationLog(Base):
    __tablename__ = "medication_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False)
    date = Column(Date, nullable=False)
    taken = Column(Boolean, default=False)
    taken_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="med_logs")
    medication = relationship("Medication")


class SleepLog(Base):
    __tablename__ = "sleep_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    date = Column(Date, nullable=False)
    hours = Column(Float, default=0)
    quality = Column(Integer, default=3)  # 1-5

    user = relationship("User", back_populates="sleep_logs")


class PeriodLog(Base):
    __tablename__ = "period_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    date = Column(Date, nullable=False)
    flow_intensity = Column(String(20))
    symptoms = Column(Text)
    phase = Column(String(30))
    cycle_day = Column(Integer, nullable=True)
    notes = Column(Text)

    user = relationship("User", back_populates="period_logs")


class Allergy(Base):
    __tablename__ = "allergies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    allergen = Column(String(200), nullable=False)
    severity = Column(String(50))
    reaction = Column(Text)
    emergency_contact = Column(String(200))
    emergency_phone = Column(String(50))

    user = relationship("User", back_populates="allergies")


class MoodLog(Base):
    __tablename__ = "mood_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    date = Column(Date, nullable=False)
    mood = Column(Integer, default=3)  # 1-5
    energy = Column(Integer, default=3)  # 1-5
    stress = Column(Integer, default=3)  # 1-5
    notes = Column(Text)

    user = relationship("User", back_populates="mood_logs")


class GoalSettings(Base):
    __tablename__ = "goal_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), unique=True, nullable=False)
    water_ml = Column(Integer, default=3000)
    calories = Column(Integer, default=2000)
    exercise_min = Column(Integer, default=30)
    sleep_hours = Column(Float, default=8.0)

    user = relationship("User", back_populates="goals")


class WeightLog(Base):
    __tablename__ = "weight_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    date = Column(Date, nullable=False)
    weight_kg = Column(Float, nullable=False)
    bmi = Column(Float, nullable=True)
    notes = Column(Text, default="")

    user = relationship("User", back_populates="weight_logs")

# 🐖 Pig Management System - Fattening Flock Feature Development Workflow

This document outlines the development stages and tasks for integrating a **Fattening Flock Monitoring** feature into the existing Flask + SQLite-based pig management system.

---

## 🧩 Stage 1: Database Planning & Schema Design

### ✅ Tasks:
- Review current sow and piglet tables.
- Create new tables to manage fattening groups and pig records.

### 🗂️ Suggested Tables:
1. **fattening_groups**
   - `id`: Primary Key
   - `litter_number`: Unique
   - `date_created`
   - `notes` (optional)

2. **fattening_pigs**
   - `id`: Primary Key
   - `fattening_group_id`: Foreign Key → `fattening_groups.id`
   - `pig_number`: Unique per group (auto-assigned: 'PIG 1', 'PIG 2', ...)
   - `weight_records`: (optional JSON or separate table)
   - `medical_records`: (optional JSON or separate table)

3. **weight_records**
   - `id`: Primary Key
   - `fattening_pig_id`: Foreign Key → `fattening_pigs.id`
   - `date_recorded`
   - `weight`

4. **medical_records**
   - `id`: Primary Key
   - `fattening_pig_id`: Foreign Key → `fattening_pigs.id`
   - `date_administered`
   - `treatment`

---

## 🏗️ Stage 2: Backend Logic (Flask Routes & Models)

### ✅ Tasks:
- Define SQLAlchemy models for the new tables.
- Set up routes:
  - `/fattening_groups/create` - Create a new group from selected piglets.
  - `/fattening_groups/<id>` - View group details and pig list.
  - `/fattening_pigs/<id>` - View/edit individual pig details (weights, medical records).
- Auto-generate `pig_number` per pig in the group.

---

## 🧮 Stage 3: Litter Number Integration

### ✅ Tasks:
- Modify group creation logic to:
  - Pull piglets from existing sow service records.
  - Enforce **unique litter number** globally.
  - Require user to select a sow's piglets and specify a unique litter number.
- Validate:
  - Only one group per litter number.
  - Pig numbers auto-increment starting from 1 for each group.

---

## 🧑‍💻 Stage 4: User Interface (HTML Forms & Pages)

### ✅ Tasks:
- Design forms and pages:
  - [ ] **Create Group** form: Select sow > Select piglets > Enter unique litter number.
  - [ ] **Group Details Page**: Show pig list, litter number, age info.
  - [ ] **Pig Details Page**: Form to log weight & medication.

---

## 🧪 Stage 5: Testing & Validation

### ✅ Tasks:
- Add unit tests for:
  - Unique litter number validation.
  - Pig number assignment logic.
  - CRUD operations on medical/weight records.
- Test UI for:
  - Group creation edge cases.
  - Error handling and validation messages.

---

## 🧹 Stage 6: Cleanup, Docs & Deployment

### ✅ Tasks:
- Add UI notes and tooltips for users.
- Write brief usage documentation in admin panel or README.
- Backup DB, migrate schema if needed, and deploy new changes.

---

## 🚀 Optional Enhancements (After Launch)

- Add charts showing weight gain over time.
- Notify upcoming medication schedules.
- Export data as CSV for reporting.

---

**Notes:**  
- Piglets can still be managed by sow independently.  
- This system adds centralized fattening management **optionally**.  
- Litter numbers act as a permanent identifier across the app.


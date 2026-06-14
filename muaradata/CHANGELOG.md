## [0.2.0] - 2025-12-29
### Added
- Strategy-based insert_data
- Strategy-based generate_table
- Connection pooling
- Retry manager (decorator-based)

### Changed
- Internal architecture refactor
- Public API frozen

### Deprecated
- credential_connection


## [0.2.1] - 2025-12-31
### Changed
- File Structure
- Add Auto-Detect data type for insert_data


## [0.2.2] - 2026-03-16

### Changed
- Add Feature: Connect DB via SSH Tunnel

### Added
- Menambahkan Command Line Interface (CLI) melalui `entry_points`.
- Alias perintah `iriisdb` untuk menjalankan manajemen kredensial (`manage_credentials`).
- Alias perintah `test_iriisdb` untuk menjalankan unit testing.

### Fixed
- Memperbaiki struktur package agar mendukung fungsi callable dari terminal.

## [0.2.3] - 2026-04-21

### Fixed 
- Memperbaiki proses transformasi untuk tipe data Array

## [0.2.4] - 2026-04-25

### Fixed 
- Clean and Safe Code

## [0.2.5] - 2026-04-29

### Added
- Loading Status
- Managing credential file 
- Add API avail_data and copy_table

## [0.2.6] - 2026-05-04

### Added
- Encripted credential and tunnel config file

## [0.2.7] - 2026-05-10

### Added
- Refactor credential manager

## [0.2.8] - 2026-06-02

### Fixing		
- Credential Manager key
- Simplify API file

### Added
- Function Copy Table 
- Driver MySQL All function
INSERT INTO chatbot.users (username,email,hashed_password,full_name,is_active,created_at,updated_at,user_role) VALUES
	 ('normal_user@example.com','normal_user@example.com','$2b$12$3Kq3KJXpVYAXITMPuGWWK.rGx7Q.1hkSORSu3plQ8xpjetauHVTu2','normal_user',true,'2026-01-13 10:24:09.444277+08','2026-01-13 10:24:09.444277+08','normal_user'::chatbot."user_role_enum"),
	 ('admin','admin@example.com','$2b$12$sNri.njCr/2scQIycHItuupio35Zp04Ed8aPTJi4uTn4csNxxdkx.','admin',true,'2025-11-30 09:33:53.785846+08','2025-11-30 09:33:53.785846+08','superadmin'::chatbot."user_role_enum"),
	 ('admin1@example.com','admin1@example.com','$2b$12$sNri.njCr/2scQIycHItuupio35Zp04Ed8aPTJi4uTn4csNxxdkx.','admin1',true,'2026-01-14 17:41:05.794892+08','2026-01-14 17:41:05.794892+08','superadmin'::chatbot."user_role_enum");




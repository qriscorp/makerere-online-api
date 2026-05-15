-- Admin user setup
UPDATE users SET name='Bashir', email='bashkiko@gmail.com', password=MD5('admin123'), super_admin='1', access='{"academics":"1","exam":"1","student":"1","teacher":"1","extra_class":"1","homework":"1","video":"1","payment":"1","settings":"1","frontend":"1","doubts":"1","library":"1","certificate":"1"}' WHERE id=1;

-- Add missing column for PHP compatibility
ALTER TABLE users ADD COLUMN IF NOT EXISTS contact_no VARCHAR(50) NOT NULL DEFAULT '' AFTER email;

-- Site branding
UPDATE site_details SET site_title='Makerere Online School', site_logo='makerere_logo.png', site_minilogo='makerere_logo.png', site_favicon='makerere_logo.png', copyright_text='Copyright © 2025 Makerere Online School. All Rights Reserved.' WHERE id=1;

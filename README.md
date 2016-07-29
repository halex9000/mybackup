# mybackup.py

Usage: python mybackup.py myconfig.ini

# myconfig.ini

First Row (Config sending email after backup)
[CONFIG_MAIL];1;emailfrom@domain.org;emailto@domain.org;smtpserver

#[CONFIG_MAIL]; Don't remove
#Start Email after backup;	0 = No, 1 = YES
#EmailFrom;		Email From
#EmailTo;			Email To
#RelaySmtp;		SMTP Server to send email

Each row after contain a single backup command 

#CopyType;Dir_From;Dir_To;Zip_File;Incremental;FilePrefix;FormatDate;MySQLHost;MySQL_DB;MySQL_User;MySQL_Pass

#CopyType; 		0 = Single File/Dir, 1 = SubDirRecurse, 2 = Mirror (NO ZIP)
#Dir_From; 		Start Dir
#Dir_To; 		  Destination Dir
#Zip_File;		0 = No, 1 = YES. 
#Incremental; 	0 = No, 1 = YES. Incremental backup, just daily touched file
#FilePrefix;	Prefix string file (just zip or mysql dump)
#FormatDate;Unix mode => %Y%m%d_%H%M%S = AAAAMMGG_HHMMSS
#MySQLHost;		MySQL Host address
#MySQL_DB;		DB Name. ['db1','db2'] or * for all
#MySQL_User;	Admin name
#MySQL_Pass;	Admin password

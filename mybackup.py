##########################################################################################################################################################
#
PROGRAM="mybackup.py"
AUTHOR="Alessandro Carichini (C) 2016"
VERSION = "1.716b"
#    Date: 13-06-2016
#  Update: 24-07-2016
#
#    Note: Backup file server
#        : Legge file mybackup.ini contenete l'elenco dei file da copiare
#        : Creazione di file zip incrementali, Dump DB MySQL, 
#        : Fix campi numerici e stringa con replace apice
###########################################################################################################################################################    
# Module: MySQLdb
##########################################################################################################################################################
# File Configurazione mybackup.ini
##########################################################################################################################################################
#[CONFIG_MAIL]; Etichetta fissa per indicare la configurazione per l'invio della email
#InvioEmail;	0 = No, 1 = Si
#EmailFrom;		Indirizzo email mittente
#EmailTo;		Indirizzo email destinatario
#---------------------------------------------------------------------------------------------------------------------------
#TipoCopy;Dir_From;Dir_To;Zip_File;Incremental;FilePrefix;FormatDate;MySQLHost;MySQL_DB;MySQL_User;MySQL_Pass
#---------------------------------------------------------------------------------------------------------------------------
#TipoCopy; 		0 = Singolo File/Dir, 1 = SubDirRecurse, 2 = Mirror (solo per copie no zip)
#Dir_From; 		Directory di partenza (inserendo il file con percorso fa la copia del singolo file)
#Dir_To; 		Directory di arrivo
#Zip_File;		0 = No, 1 = Si. Genera un file zip anziche' la copia dei file
#Incremental; 	0 = No, 1 = Si. Fa backup incrementale (solo file toccati in giornata) anziche' globale 
#             	Quindi il backup deve essere lanciato lo stesso giorno delle modifiche (quotidiano)
#FilePrefix;	Parte fissa del nome del file (solo per Zip Appare dopo Il FormatData)
#FormatDate;	Formato della data nel nome file (Unix mode => %Y%m%d_%H%M%S = AAAAMMGG_HHMMSS)
#MySQLHost;		Indirizzo dell'Host MySQL
#MySQL_DB;		Nome database da copiare o lista all'interno di un array ['db1','db2']
#             	Inserendo * prende tutti i database
#MySQL_User;	User amministratore per l'accesso MySQL
#MySQL_Pass;	Password amministratore MySQL
##########################################################################################################################################################

try:
	import MySQLdb
except:
	print "Install MySQLdb"
	print "Win32 => https://pypi.python.org/pypi/MySQL-python/"	
	print "Linux => apt-get install python-mysqldb"	
	exit(1)
	
import datetime
import glob
import os 
import string
import os.path
import sys
import zipfile
import hashlib
import time
import shutil
import smtplib
from email.mime.text import MIMEText
import platform
import getopt

FILEINI = "mybackup.ini"

if len(sys.argv) == 2:
	XFILEINI = sys.argv[1]
	
	if os.path.isfile(XFILEINI):
		FILEINI = XFILEINI
	else: 
		if not os.path.isfile(FILEINI):
			print "Configuration File Missing!"
			exit(1)
		
# OS_TYPE:
# 
# 0 = UNIX
# 1 = WINDOWS
#

OS_TARGA = platform.system()

if OS_TARGA == "Windows":
	OS_TYPE = 1
else:
	OS_TYPE = 0

if OS_TYPE == 1:
	OS_SLASH = "\\"
else:
	OS_SLASH = "/"

################################################################################################################################### SUBS

def FileDate(filename):
	return time.strftime("%d%m%Y",time.localtime(os.path.getmtime(filename)))

def SendMail(mailfrom,mailto,mailobj,mailmsg,smtp):
	msg = MIMEText(mailmsg)
	
	msg['Subject'] = mailobj
	msg['From'] = mailfrom
	msg['To'] = mailto
	
	s = smtplib.SMTP(smtp)
	s.sendmail(mailfrom, mailto, msg.as_string())
	s.quit()

def CopyFiles(Dir_Source,Dir_Dest):
	result = 0
	dirList = glob.glob(dir+"*.*")
	for fileN in (dirList):
		if os.path.isfile(fileN): 
			try:
				shutil.copy(Dir_Source+fileN, Dir_Dest+fileN)
			except shutil.Error as e:
				result = e
			except IOError as e:
				result = e

	return result

def XCopy(Dir_Source,Dir_Dest,Incremental,TipoCopy):
	result = 0
	
	# SubDir Recurse 
	if (TipoCopy == 1):
		dirList = glob.glob(dir+"*.*")
		for fileN in (dirList):
			if os.path.isfile(fileN): 
				try:
					shutil.copy(Dir_Source+fileN, Dir_Dest+fileN)
				except shutil.Error as e:
					result = e
				except IOError as e:
					result = e
	if (TipoCopy == 2):
		if OS_TYPE == 0:
			cmd = "rsync -av --delete-after "+Dir_Source+"/* "+Dir_Dest
		else:
			cmd = "robocopy "+Dir_Source+" "+Dir_Dest+" /MIR"
		
		result = os.system(cmd)
	else:
		if (Incremental == 1):
			print "Backup Incrementale"
			if Zip_File == 0:
				cmd = cmd + " /MAXAGE:1"

	return result
	

def DelAllFiles(dir):
	dirList = glob.glob(dir+"*.*")
	for fileN in (dirList):
		if os.path.isfile(fileN): 
#			print "delete "+str(fileN)
			os.remove(fileN)

def ZipDateToTimeStamp(dtime):
	return str(dtime[0])+"-"+str(dtime[1])+"-"+str(dtime[2])+" "+str(dtime[3])+":"+str(dtime[4])+":"+str(dtime[5])


def MakeZipFile(output_filename, source_dir, SubDir, Incremental):
	relroot = os.path.abspath(os.path.join(source_dir, os.pardir))
	result = 0
	
	# DATA OGGI
	DTODAY = str(time.strftime("%d%m%Y"))
	
	if (os.path.isfile(source_dir)):
		SubDir = 0
	
	iwrite = 0
	if (SubDir == 1):
		with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zip:
			for root, dirs, files in os.walk(source_dir):
				# add directory (needed for empty dirs)
				zip.write(root, os.path.relpath(root, relroot))
				for file in files:
					filename = os.path.join(root, file)
					if os.path.isfile(filename): # regular files only
						arcname = os.path.join(os.path.relpath(root, relroot), file)
						if Incremental == 1:
							DFILE = FileDate(filename)
							if DFILE == DTODAY:
								bWrite = 1
							else:
								bWrite = 0
						else:
							bWrite = 1
						
						if bWrite == 1:
							zip.write(filename, arcname)
							iwrite=iwrite + 1
	else:
		if os.path.isdir(source_dir):
			dir = glob.glob(source_dir+"*.*")
			zip = zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED)
			for file in (dir):
				if Incremental == 1:
					DFILE = FileDate(file)
					if DFILE == DTODAY:
						bWrite = 1
					else:
						bWrite = 0
				else:
					bWrite = 1
				
				if bWrite == 1:
					zip.write(file, os.path.basename(file))
					iwrite=iwrite + 1
		else:
			if (Incremental == 1):
				bWrite = 0
				DFILE = FileDate(source_dir)
				
				if DFILE == DTODAY:
					bWrite = 1
				else:
					bWrite = 0
			else:
				bWrite = 1
			
			if bWrite == 1:
				zip = zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED)
				try:
					zip.write(source_dir, os.path.basename(source_dir))
					iwrite=iwrite + 1
				finally:
					zip.close()
		
	if (iwrite == 0):
		if os.path.isfile(output_filename): 
			os.remove(output_filename)
	
	return iwrite


def MySQLDBList(DB_HOST,DB_USER,DB_USER_PASSWORD):
	try:
		con = MySQLdb.connect(DB_HOST,DB_USER,DB_USER_PASSWORD,"mysql")
		cur = con.cursor()

	except MySQLdb.Error, e:
		print "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
		return MySQLdb.Error

	cur.execute("SHOW DATABASES")
	dbname = []
	
	dblist = ""
	for dbnames in cur.fetchall():
		dbname.append(dbnames[0])

	con.close()
	
	return dbname

def is_number(s):
	try:
		float(s)
		return True
	except ValueError:
		pass
 
	try:
		import unicodedata
		unicodedata.numeric(s)
		return True
	except (TypeError, ValueError):
		pass
 
	return False

def MySQLDump(DB_HOST,DB_USER,DB_USER_PASSWORD,DBN,FileDumpSql):
	result = 0
	
	try:
		con = MySQLdb.connect(DB_HOST,DB_USER,DB_USER_PASSWORD,DBN)
		cur = con.cursor()

	except MySQLdb.Error, e:
		print "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
		return MySQLdb.Error

	cur.execute("SHOW TABLES")
	data = ""
	tables = []

	data += "-- MySQL Dump Generator: "+PROGRAM+" ("+VERSION+")\n"
	data += "-- by "+AUTHOR+"\n"
	data += "--\n"
	data += "-- Host: "+DB_HOST+"    Database: "+DBN+"\n"
	data += "-- ------------------------------------------------------\n"
	data += "-- Date: "+ str(time.strftime('%d-%m-%Y %H:%M:%S'))+"\n\n\n"
	
	data += "use "+DBN+";\n\n"
	
	for table in cur.fetchall():
		tables.append(table[0])

	for table in tables:
		data += "--\n"
		data += "-- Table structure for table `"+str(table)+"`\n"
		data += "--\n\n"

		data += "DROP TABLE IF EXISTS `" + str(table) + "`;"

		cur.execute("SHOW CREATE TABLE `" + str(table) + "`;")
		data += "\n" + str(cur.fetchone()[1]) + ";\n\n"

		cur.execute("SELECT * FROM `" + str(table) + "`;")

		data += "--\n"
		data += "-- Dumping data for table `"+str(table)+"`\n"
		data += "--\n\n"

		for row in cur.fetchall():
			data += "INSERT INTO `" + str(table) + "` VALUES("
			first = True
			for field in row:
				if not first:
					data += ', '

				if isinstance(field, (int, long, float, complex)):
					data += str(field) 
				else:
					if isinstance(field, basestring):
						fieldX = field.replace("'","''")
					else:
						fieldX = str(field)
						
					data += "'" + fieldX + "'"
					
				first = False

			data += ");\n"
		data += "\n\n"

	try:
		FILE = open(FileDumpSql,"w")
		FILE.writelines(data)
		FILE.close()
	except:
		result = 999
	
	con.close()
	
	return result

################################################################################################################################### MAIN APP

ibackup = 0
bSendMail = 0

msg = "MyBackup "+VERSION+" - Platform: "+OS_TARGA+"\n\n"

print msg
print "Config File: "+FILEINI

# Read Configuration File mybackup.ini
f = open(FILEINI,'r')

while 1:
	line = f.readline()
	if not line:
		break
	campi = line.split(";")
	totcampi = len(campi)

	if totcampi > 1:
		if line[:1] != "#":
			TipoRec = campi[0].strip()
			
			if TipoRec == "[CONFIG_MAIL]":
				bSendMail = int(campi[1])
				if bSendMail == 1:
					MAILFROM = campi[2].strip()
					MAILTO = campi[3].strip()
					SMTP_RELAY = campi[4].strip()
					
			else:
				ibackup=ibackup+1
				TipoCopy = int(campi[0])
				Dir_From = campi[1].strip()
				Dir_To = campi[2].strip()
				Zip_File = int(campi[3])
				Incremental = int(campi[4])
				File_Prefix = campi[5].strip()
				FormatDate = campi[6].strip()
				MySQL = 0
				text = line
				if totcampi > 7:
					MySQL_Host = campi[7].strip()
					MySQL_DB = campi[8].strip()
					MySQL_User = campi[9].strip()
					MySQL_Pass = campi[10].strip()
					MySQL = 1
					if len(MySQL_Pass) > 1:
						text = line.replace(MySQL_Pass,"******")
					
	#			print Dir_From
	#			print Dir_To		
				DATETIME = str(time.strftime(FormatDate))
				
				
				msg = msg + "("+str(ibackup)+") == BAK_CONFIG: "+text + "\n"
				DATETIMEX = str(time.strftime('%Y%m%d-%H%M%S'))
				
				if (MySQL == 0):
					print "Backup Files"
						
					if (Zip_File == 1):
						FileZIP = Dir_To+DATETIME+File_Prefix+".zip"

						if MakeZipFile(FileZIP,Dir_From, TipoCopy, Incremental) > 0:
							msg = msg + DATETIMEX+" - ZIP " +FileZIP +"\n"
							print "Creo ZIP "+ FileZIP
						else:
							msg = msg + DATETIMEX+" - NO BACKUP \n"
							print "Skip ZIP "+ FileZIP
						
					else:
						msg = msg + DATETIMEX + " - XCOPY " +Dir_From +"\n"

						if (TipoCopy > 0):
							XCopy(Dir_From,Dir_To,Incremental,TipoCopy)
						else:
							CopyFiles(Dir_From,Dir_To)
					
				else:
					print "Backup MySQL"

					# Convert db list into array
					if (MySQL_DB[0:1] == "["):
						MySQL_DB = MySQL_DB.replace("[","")
						MySQL_DB = MySQL_DB.replace("]","")
						MySQL_DB = MySQL_DB.replace("'","")
						aDB = MySQL_DB.split(",")		
					else:
						if (MySQL_DB[0:1] != "*"):
							aDB = aDB.append(MySQL_DB)
						else:
							aDB = MySQLDBList(MySQL_Host,MySQL_User,MySQL_Pass)
											
					PathAPPO = str(os.getenv("TEMP")) + OS_SLASH+"MYBACKUP"+OS_SLASH
					
					if not os.path.exists(PathAPPO):
						os.makedirs(PathAPPO)
					else:
						DelAllFiles(PathAPPO)
					
					for DBN in aDB:
						DATETIME = str(time.strftime(FormatDate))
						print "MySQL DB Dump: " + DBN			
						msg = msg + DATETIMEX +" - MySQL DumpDB: " +DBN+ "\n"
						fileAPPO = PathAPPO+DBN+".sql"
						MySQLDump(MySQL_Host,MySQL_User,MySQL_Pass,DBN,fileAPPO)
							
					if Zip_File == 1:
						MakeZipFile(Dir_To+OS_SLASH+DATETIME+File_Prefix+".zip", PathAPPO, 0,0)		
					else:
						CopyFiles(PathAPPO,Dir_To)
					
				msg = msg + "==========================================================================\n\n"

			
if bSendMail == 1:
	SendMail(MAILFROM,MAILTO,"MyBackup Report",msg,SMTP_RELAY)
				
f.close()

print "Totale Backups:  %d " % ibackup

# -*- coding: UTF-8 -*-

import socket
import threading
import MySQLdb
import time

#TODO
# 1 - No debe salir el propio usuario en la lista de usuarios - HECHO
# 2 - Recepción asíncrona de mensajes
# 3 - Envío de mensajes - HECHO
# 4 - Acceso Automatica - HECHO
# 5 - Aumentar campos en base de datos (estado del usuario (disponible, ocupado, etc))
# 6 - Guardar historial de conversaciones y que las conversaciones aparezcan en la aplicación - HECHO
# 7 - Mejora gŕafica de la aplicación en general (véase Activity de mensajes, mostrar nombre, hora etc...) (Avatar en usuarios...)
# 8 - Mejora de la Seguridad, mandar los datos cifrados y autenticados para impedir la suplantación de identidad
# 9 - Notificación de Mensajes
# 10 - Mejoras de la programación en general

# class EnvioMensajes(threading.Thread):
# 	def __init__ ( self, channel, details, usuario ):

# 		self.channel = channel
# 		self.details = details
# 		self.db=MySQLdb.connect(host='',user='', passwd='',db='')
# 		self.usuario = usuario
# 		self.salir = 0
# 		self.channel.settimeout(2)
# 		threading.Thread.__init__ ( self )

# 	def run (self):
# 		while (True):
# 			time.sleep(2)
# 			cursor = self.db.cursor()
# 			print "Enviando mensajes asincronos al cliente"
# 			sql = "SELECT MID, mensaje, emisor, timestamp FROM mensajes WHERE destinatario='"+ self.usuario + "'"
# 			print sql
# 			cursor.execute(sql)
# 			resultado=cursor.fetchall()
# 			for registro in resultado:
# 				datos = "0x05|"+str(len(registro[1]))+"|"+registro[1]+"|"+str(len(registro[2]))+"|"+registro[2]+"|"+str(len(registro[3]))+"|"+registro[3]+"\n"
# 				time.sleep(3)
# 				self.channel.send(datos)
# 				print datos[:-1]
# 				print "Esperando confirmación del cliente"
# 				confirmacion = self.channel.recv(len(datos))
# 				print confirmacion
# 				if confirmacion[:-1] == datos[:-1]:
# 					sql = "DELETE FROM mensajes WHERE MID="+str(registro[0])
# 					cursor.execute(sql)
# 					print sql



class Servidor ( threading.Thread ):

	def __init__ ( self, channel, details ):

		self.channel = channel
		self.details = details
		self.db=MySQLdb.connect(host='',user='', passwd='',db='')
		self.conectado = 0
		self.salir = 0
		self.channel.settimeout(3)
		threading.Thread.__init__ ( self )


	def run ( self ):
		print "Nuevo Cliente Conectado"
		while self.salir != 1:
			datos = ""
			datos = self.channel.recv(1000)
			time.sleep(2)
			print datos[:-1]
			campos = datos.split("|")
			if campos[0] == "0x01":
				print "Solicitud recibida: 0x01 AUTENTICACIÓN"
				#0x01|4|RdlP|32|937dd5a27716b758ec7a705430a7cecf
				nombre = campos[2]
				password = campos[4]
				print "Nombre: "+nombre
				print "Contraseña introducida: "+password[:-1]
				cursor = self.db.cursor()
				sql = "SELECT nombre, password FROM usuarios WHERE nombre='"+nombre+"'"
				cursor.execute(sql)
				resultado=cursor.fetchall()
				print "Contraseña guardada en la Base de Datos: "+ resultado[0][1]
				if resultado[0][1] == password[:-1]:
					print "El usuario "+nombre+" se ha autenticado correctamente"
					self.usuario = nombre
					self.conectado = 1
					datos="0x00|Usuario autenticado correctamente\n"
					self.channel.send(datos)
					
				else:
					print "El usuario "+ nombre + " falló en su autenticación"
					self.conectado = 0
					datos="0x40|El usuario no se pudo autenticar\n"
					self.channel.send(datos)
			if (self.conectado == 1) and (datos != ""):
				if campos[0][:-1] == "0x02":
					print "Solicitud recibida: 0x02 Petición de Usuarios"
					cursor = self.db.cursor()
					sql = "SELECT nombre, last_online FROM usuarios WHERE nombre NOT IN ('" + nombre + "')"
					print sql
					cursor.execute(sql)
					resultado=cursor.fetchall()
					for registro in resultado:
						datos = "0x02|"+str(len(registro[0]))+"|"+registro[0]+"|"+str(len(registro[1]))+"|"+registro[1]+"\n"
						time.sleep(3)
						self.channel.send(datos)
						print datos[:-1]
					datos = "0xFF\n"
					self.channel.send(datos)
				elif campos[0] == "0x03":
					print "Solicitud recibida: 0x03 Petición de Mensajes Pendientes"
					cursor = self.db.cursor()
					sql = "SELECT MID, mensaje, emisor, timestamp FROM mensajes WHERE destinatario='"+ campos[2][:-1] + "'"
					print sql
					cursor.execute(sql)
					resultado=cursor.fetchall()
					for registro in resultado:
						datos = "0x03|"+str(len(registro[1]))+"|"+registro[1]+"|"+str(len(registro[2]))+"|"+registro[2]+"|"+str(len(registro[3]))+"|"+registro[3]+"\n"
						time.sleep(3)
						self.channel.send(datos)
						print datos[:-1]
						print "Esperando confirmación del cliente"
						confirmacion = self.channel.recv(len(datos))
						print confirmacion
						if confirmacion[:-1] == datos[:-1]:
							sql = "DELETE FROM mensajes WHERE MID="+str(registro[0])
							cursor.execute(sql)
						print sql
						#TODO El servidor necesita confirmación de que el mensaje ha llegado al cliente, y una vez le llegue esta confirmación deberá borrar el mensaje de la base de datos
					datos = "0xFF\n"
					self.channel.send(datos)
					#EnvioMensajes(self.channel, self.details, nombre).start()

				elif campos[0] == "0x04":
					print "Solicitud recibida: 0x04 El cliente quiere enviar un mensaje"
					emisor = campos[2]
					destinatario = campos[4]
					mensaje = campos[6][:-1]
					timestamp = "ahora"
					cursor = self.db.cursor()
					sql = "INSERT INTO mensajes (MID, mensaje, destinatario, emisor, timestamp) VALUES (NULL,'" + mensaje +"','"+ destinatario + "','"+ emisor+"','"+timestamp+"')"
					print sql
					cursor.execute(sql)
					self.channel.send(datos)
			else:
				time.sleep(2)
				cursor = self.db.cursor()
				print "Enviando mensajes asincronos al cliente"
				sql = "SELECT MID, mensaje, emisor, timestamp FROM mensajes WHERE destinatario='"+ self.usuario + "'"
				print sql
				cursor.execute(sql)
				resultado=cursor.fetchall()
				for registro in resultado:
					datos = "0x05|"+str(len(registro[1]))+"|"+registro[1]+"|"+str(len(registro[2]))+"|"+registro[2]+"|"+str(len(registro[3]))+"|"+registro[3]+"\n"
					time.sleep(3)
					self.channel.send(datos)
					print datos[:-1]
					print "Esperando confirmación del cliente"
					confirmacion = self.channel.recv(len(datos))
					print confirmacion
					if confirmacion[:-1] == datos[:-1]:
						sql = "DELETE FROM mensajes WHERE MID="+str(registro[0])
						cursor.execute(sql)
						print sql



server = socket.socket ( socket.AF_INET, socket.SOCK_STREAM )
server.bind ( ( '', 2727 ) )
server.listen ( 1000 )


# Have the server serve "forever":
while True:
	channel, details = server.accept()
	Servidor ( channel, details ).start()


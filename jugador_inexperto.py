# Practicando implementaciones de jugador
# Este jugador sigue algunas reglas del archivo de inteligencia
# Deberia ganarle a JugadorAprendiz

from constantes import *
from jugador import Jugador
from probabilidad import Probabilidad, proba

# Ejercitos (sin contar el obligatorio) a dejar en paises de orden 2.
EXTRA_ORDEN2 = 2

class JugadorInexperto(Jugador):
	""" Segundo prototipo de un jugador inteligente.
	"""
	def _limita_con(self, tablero, pais, condicion):
		""" Recibe un pais, devuelve True si 
		algun limite cumple con la condicion.
		"""
		if not self.es_mi_pais(tablero, pais):
			raise ValueError("No es tu pais!")
		for limitrofe in tablero.paises_limitrofes(pais):
			if condicion(tablero, limitrofe):
				return True
		return False
	
	def es_mi_pais(self, tablero, pais):
		return self.color == tablero.color_pais(pais)
	
	def es_enemigo(self, tablero, pais):
		return not self.es_mi_pais(tablero, pais)
		
	def es_frontera(self, tablero, pais):
		""" Devuelve True si el pais limita con algun pais enemigo.
		"""
		return self._limita_con(tablero, pais, self.es_enemigo)
	
	def orden_proteccion(self, tablero):
		""" Devuelve un diccionario con tus paises 
		de clave y la cantidad de paises que 
		lo protegen (incluyendose) como valor.
		"""
		orden_proteccion = {}
		paises = tablero.paises_color(self.color)
		for pais in paises:
			if self.es_frontera(tablero, pais):
				orden_proteccion[pais] = 1
			else:
				orden_proteccion[pais] = 100 #Numero absurdo: El maximo orden es 9 o 10
		while 100 in orden_proteccion.values():
			for pais in orden_proteccion:
				for limitrofe in tablero.paises_limitrofes(pais):
					if limitrofe not in paises:
						continue
					orden_proteccion[limitrofe] = min(orden_proteccion[limitrofe], orden_proteccion[pais]+1)
		return orden_proteccion
	
	def agregar_ejercitos(self, tablero, cantidad):
		# Esto tiene el problema de que agrega ejercitos en bloque.
		jugada = {}
		for continente, cantidad_continente in sorted(cantidad.items(), reverse=True):
			paises_posibles = tablero.paises(continente)
			for i, pais in enumerate(paises_posibles):
				if tablero.color_pais(pais) != self.color:
					continue
				# Si en todos da False, agrega en el ultimo
				if i != len(paises_posibles) - 1 and not self.quiero_agregar(tablero, pais):
					continue
				jugada[pais] = jugada.get(pais, 0) + cantidad_continente
				break
		return jugada
		
	def quiero_agregar(self, tablero, pais):
		""" Informa si el pais es una buena opcion para agregar ejercitos """
		# Quiero agregar si algun pais vecino es enemigo
		return self.es_frontera(tablero, pais)
	
	def atacar(self, tablero, paises_ganados_ronda):
		mis_paises = tablero.paises_color(self.color)
		for pais in mis_paises:
			for limitrofe in tablero.paises_limitrofes(pais):
				# no me quiero atacar a mi mismo
				if tablero.color_pais(limitrofe) == self.color:
					continue
				# Estrenando las probabilidades
				if self.quiero_atacar(tablero, pais, limitrofe, 0.51):
					return pais, limitrofe
		return None
		
	def quiero_atacar(self, tablero, origen, destino, proba_aceptada):
		""" Informa si el pais de destino es una buena opcion para atacar. Recibe
		la probabilidad de exito aceptable y devuelve True si la probabilidad real
		la iguala o supera.
		"""
		return (proba.ataque(tablero.ejercitos_pais(origen), 
				tablero.ejercitos_pais(destino)) >= proba_aceptada)

	def mover(self, origen, destino, tablero, paises_ganados_ronda):
		""" Se ejecuta al ocupar un pais y devuelve la cantidad de ejercitos
		de ocupacion."""
		# Muevo la mayor cantidad de ejercitos posible, evitando que el origen 
		# quede con menos ejercitos que 1+EXTRA_ORDEN2.
		return max(1, min(3, tablero.ejercitos_pais(origen) - EXTRA_ORDEN2 - 1))
	
	def reagrupar(self, tablero, paises_ganados_ronda):
		""" Mueve todos los ejercitos de un pais a paises 
		de orden inferior. En caso de orden 2, se quedara 
		con 3 si puede.
		NO FUNCIONA! No se porque hace levantar error en dados.
		Tal vez estoy pidiendo movimientos ilegales sin darme cuenta...
		"""
		reagrupamientos = []
		# Lleva la cuenta de los ejercitos disponibles para reagrupar de los
		# paises involucrados en esta ronda (Para evitar el traslado de ejercitos
		# en cadena)
		ejercitos_reagrupables = {}
		for pais in tablero.paises_color(self.color):
			ejercitos_reagrupables[pais] = tablero.ejercitos_pais(pais) - 1
		
		orden_proteccion = self.orden_proteccion(tablero)
		orden_a_mover = max(orden_proteccion.values())
		while orden_a_mover >= 2:
			paises_a_mover = [pais for pais in orden_proteccion if orden_proteccion[pais] == orden_a_mover]
			orden_pais = orden_a_mover
			for pais in paises_a_mover:
				# Defino quienes van a ser los que reciban algo de este pais.
				limitrofes_a_recibir = [limitrofe for limitrofe in tablero.paises_limitrofes(pais) if (
					limitrofe in orden_proteccion and orden_proteccion[limitrofe] < orden_pais)]
				
				# Les reparto a cada uno una cantidad igual de todos mis ejercitos.
				ejercitos_a_enviar = ejercitos_reagrupables[pais]
				# En caso de que el pais sea de orden 2, repartira pero quedandose con EXTRA_ORDEN2 al final si es posible.
				if orden_pais == 2:
					ejercitos_a_enviar = max(ejercitos_a_enviar - EXTRA_ORDEN2, 0)
				
				if not ejercitos_a_enviar:
					continue
				
				
				for limitrofe in limitrofes_a_recibir:
					ejercitos_reagrupables[pais] -= ejercitos_a_enviar/len(limitrofes_a_recibir)
					reagrupamientos.append( (pais, limitrofe, ejercitos_a_enviar/len(limitrofes_a_recibir)) )
					tablero.actualizar_interfaz(self.cambios(reagrupamientos))
				
				# Reparto los que sobraron.
				ejercitos_restantes = ejercitos_a_enviar % len(limitrofes_a_recibir)
				if not ejercitos_restantes:
					continue
				for x in xrange(ejercitos_restantes):
					ejercitos_reagrupables[pais] -= 1
					reagrupamientos.append( (pais, limitrofes_a_recibir[x], 1) )
					tablero.actualizar_interfaz(self.cambios(reagrupamientos))
					
			orden_a_mover -= 1
			
		# ACA ME FALTA IMPLEMENTAR QUE UNA FRONTERA LE PASE EJERCITOS A OTRA SI HACE FALTA PARA MAXIMIZAR LA SEGURIDAD.
		return reagrupamientos
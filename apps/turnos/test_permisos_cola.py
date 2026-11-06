from django.test import TestCase, RequestFactory
from .helpers_tests import Escenario, crear_barbero, crear_usuario
from .permisos import personal_de_barberia


# Sprint 7 - Módulo D (Facundo): permisos de la cola por orden de llegada.
# Prueba el helper que usan los endpoints de la cola (apps/turnos/permisos.py).

class PermisosColaTests(Escenario, TestCase):
    def setUp(self):
        self.crear_escenario()
        self.bo_dueno = crear_barbero(self.d1, self.b1)    # d1: dueño-barbero de B1

    def pedido(self, usuario=None):
        request = RequestFactory().get('/')
        request.session = {}
        if usuario is not None:
            request.session['id_usuario'] = usuario.id_usuario
        return request

    def probar(self, usuario, id_barberia=None):
        barberia, barbero, error = personal_de_barberia(self.pedido(usuario), id_barberia)
        return barberia, barbero, (error.status_code if error else None)

    def test_sin_sesion(self):
        self.assertEqual(self.probar(None)[2], 401)
        self.assertEqual(self.probar(None, self.b1.id_barberia)[2], 401)

    def test_dueno_accede_a_su_barberia(self):
        barberia, barbero, status = self.probar(self.d2, self.b2.id_barberia)
        self.assertEqual((barberia, barbero, status), (self.b2, None, None))
        self.assertEqual(self.probar(self.d2)[0], self.b2)

    def test_barbero_accede_a_su_barberia(self):
        barberia, barbero, status = self.probar(self.u_bo1, self.b1.id_barberia)
        self.assertEqual((barberia, barbero, status), (self.b1, self.bo1, None))
        self.assertEqual(self.probar(self.u_bo1)[0], self.b1)

    def test_dueno_barbero(self):
        barberia, barbero, status = self.probar(self.d1, self.b1.id_barberia)
        self.assertEqual((barberia, barbero, status), (self.b1, self.bo_dueno, None))

    def test_no_se_accede_a_la_cola_de_otra_barberia(self):
        self.assertEqual(self.probar(self.d1, self.b2.id_barberia)[2], 403)
        self.assertEqual(self.probar(self.d2, self.b1.id_barberia)[2], 403)
        self.assertEqual(self.probar(self.u_bo1, self.b2.id_barberia)[2], 403)
        self.assertEqual(self.probar(self.u_bo3, self.b1.id_barberia)[2], 403)

    def test_cliente_sin_barberia(self):
        self.assertEqual(self.probar(self.c1)[2], 404)
        self.assertEqual(self.probar(self.c1, self.b1.id_barberia)[2], 403)

    def test_barberia_inactiva(self):
        self.b1.estado = 'INACTIVA'
        self.b1.save()
        self.assertEqual(self.probar(self.d1, self.b1.id_barberia)[2], 403)

# Copyright 2026 Open Source Integrators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ..services import SatClient

_SVC = "odoo.addons.l10n_mx_sat.services.sat_client"


@tagged("post_install", "-at_install")
class TestSatClient(TransactionCase):
    """Tests for the SatClient adapter (pure Python class)."""

    @patch(f"{_SVC}.Signer")
    def test_init_creates_signer(self, MockSigner):
        SatClient(b"cer", b"key", "pwd")
        MockSigner.assert_called_once_with(b"cer", b"key", "pwd")

    @patch(f"{_SVC}.SATPortal")
    @patch(f"{_SVC}.Signer")
    def test_authenticate_returns_token(self, MockSigner, MockSATPortal):
        MockSATPortal.return_value.login.return_value = "tok-123"
        client = SatClient(b"cer", b"key", "pwd")

        token = client.authenticate()
        self.assertEqual(token, "tok-123")
        MockSATPortal.assert_called_once_with(MockSigner.return_value)

    @patch(f"{_SVC}.SATPortal")
    @patch(f"{_SVC}.Signer")
    def test_authenticate_empty_token_raises(self, MockSigner, MockSATPortal):
        MockSATPortal.return_value.login.return_value = ""
        client = SatClient(b"cer", b"key", "pwd")

        with self.assertRaises(ValueError):
            client.authenticate()

    @patch(f"{_SVC}.SAT")
    @patch(f"{_SVC}.Signer")
    def test_request_download(self, MockSigner, MockSAT):
        expected = {"cod_estatus": "5000", "id_solicitud": "SOL-1"}
        MockSAT.return_value.recover_comprobante_received_request.return_value = (
            expected
        )
        client = SatClient(b"cer", b"key", "pwd")

        result = client.request_download("tok", "RFC1", "2026-01-01", "2026-01-31")

        self.assertEqual(result, expected)

    @patch(f"{_SVC}.SAT")
    @patch(f"{_SVC}.Signer")
    def test_request_download_defaults_estado_comprobante(self, MockSigner, MockSAT):
        """estado_comprobante defaults to EstadoComprobante.VIGENTE."""
        from satcfdi.models.code import EstadoComprobante

        MockSAT.return_value.recover_comprobante_received_request.return_value = {}
        client = SatClient(b"cer", b"key", "pwd")

        client.request_download("tok", "RFC1", "2026-01-01", "2026-01-31")

        call_kwargs = (
            MockSAT.return_value.recover_comprobante_received_request.call_args
        )
        self.assertEqual(
            call_kwargs.kwargs.get("estado_comprobante"), EstadoComprobante.VIGENTE
        )

    @patch(f"{_SVC}.SAT")
    @patch(f"{_SVC}.Signer")
    def test_request_download_allows_override_estado(self, MockSigner, MockSAT):
        """Caller can still override estado_comprobante if needed."""
        from satcfdi.models.code import EstadoComprobante

        MockSAT.return_value.recover_comprobante_received_request.return_value = {}
        client = SatClient(b"cer", b"key", "pwd")

        client.request_download(
            "tok",
            "RFC1",
            "2026-01-01",
            "2026-01-31",
            estado_comprobante=EstadoComprobante.CANCELADO,
        )

        call_kwargs = (
            MockSAT.return_value.recover_comprobante_received_request.call_args
        )
        self.assertEqual(
            call_kwargs.kwargs.get("estado_comprobante"), EstadoComprobante.CANCELADO
        )

    @patch(f"{_SVC}.SAT")
    @patch(f"{_SVC}.Signer")
    def test_verify_download(self, MockSigner, MockSAT):
        expected = {"estado_solicitud": "3", "paquetes": ["PKG-1"]}
        MockSAT.return_value.recover_comprobante_status.return_value = expected
        client = SatClient(b"cer", b"key", "pwd")

        result = client.verify_download("tok", "RFC1", "SOL-1")

        self.assertEqual(result, expected)
        MockSAT.return_value.recover_comprobante_status.assert_called_once_with(
            "SOL-1"
        )

    @patch(f"{_SVC}.SAT")
    @patch(f"{_SVC}.Signer")
    def test_download_package(self, MockSigner, MockSAT):
        expected = {"cod_estatus": "5000", "paquete_b64": "b64data"}
        MockSAT.return_value.recover_comprobante_package.return_value = expected
        client = SatClient(b"cer", b"key", "pwd")

        result = client.download_package("tok", "RFC1", "PKG-1")

        self.assertEqual(result, expected)
        MockSAT.return_value.recover_comprobante_package.assert_called_once_with(
            "PKG-1"
        )

    @patch(f"{_SVC}.SAT")
    @patch(f"{_SVC}.Signer")
    def test_validate_cfdi(self, MockSigner, MockSAT):
        expected = {"estado": "Vigente"}
        MockSAT.return_value.validate_cfdi.return_value = expected
        client = SatClient(b"cer", b"key", "pwd")

        result = client.validate_cfdi("RFC1", "RFC2", "100.00", "uuid-1")

        self.assertEqual(result, expected)
        MockSAT.return_value.validate_cfdi.assert_called_once_with(
            "RFC1", "RFC2", "100.00", "uuid-1"
        )

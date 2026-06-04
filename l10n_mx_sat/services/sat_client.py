# Copyright 2026 Open Source Integrators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from satcfdi.models.signer import Signer
from satcfdi.models.code import EstadoComprobante
from satcfdi.pacs.sat import SAT
from satcfdi.portal import SATPortal

_logger = logging.getLogger(__name__)


class SatClient:
    """SAT web service adapter via satcfdi.

    Pure Python class with no Odoo ORM dependency.
    Swappable through the res.company.l10n_mx_sat_get_client() factory.
    """

    def __init__(self, cer_der, key_der, password):
        """Initialize the client with FIEL credentials.

        :param cer_der: certificate in DER format (bytes)
        :param key_der: private key in DER format (bytes)
        :param password: private key password (str)
        """
        self._signer = Signer(cer_der, key_der, password)

    def authenticate(self):
        """Authenticate with the SAT and return the token.

        :raises ValueError: if the token is empty
        :return: SAT authentication token
        :rtype: str
        """
        portal = SATPortal(self._signer)
        portal.login()
        token = portal.session_token
        if not token:
            raise ValueError("SAT returned an empty token.")
        return token

    def request_download(self, rfc, fecha_inicial, fecha_final, **kwargs):
        """Send a download request to the SAT (Descarga Masiva).

        Defaults estado_comprobante to EstadoComprobante.VIGENTE.

        :return: dict with keys cod_estatus, id_solicitud, mensaje
        """
        kwargs.setdefault("estado_comprobante", EstadoComprobante.VIGENTE)
        sat = SAT(self._signer)
        return sat.recover_comprobante_received_request(
            fecha_inicial, fecha_final, rfc, **kwargs
        )

    def verify_download(self, id_solicitud):
        """Check the status of a download request.

        :return: dict with keys estado_solicitud, paquetes, numero_cfdis, mensaje
        """
        sat = SAT(self._signer)
        return sat.recover_comprobante_status(id_solicitud)

    def download_package(self, id_paquete):
        """Download a package from the SAT.

        :return: dict with keys cod_estatus, paquete_b64, mensaje
        """
        sat = SAT(self._signer)
        return sat.recover_comprobante_package(id_paquete)

    def validate_cfdi(self, rfc_emisor, rfc_receptor, total, uuid):
        """Validate a CFDI status against the SAT.

        :return: dict with keys codigo_estatus, es_cancelable, estado
        """
        sat = SAT(self._signer)
        return sat.validate_cfdi(rfc_emisor, rfc_receptor, total, uuid)

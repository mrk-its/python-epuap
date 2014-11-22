import datetime
import uuid
import base64
from urllib import urlencode

import requests
from lxml.builder import ElementMaker, ET

BASE_URL = 'https://hetman.epuap.gov.pl'
AUTHN_URL = BASE_URL + '/DracoEngine2/draco.jsf'
SAML_ARTIFACT_SVC_URL = BASE_URL + "/axis2/services/EngineSAMLArtifact"

NS_SAMLP = "urn:oasis:names:tc:SAML:2.0:protocol"
NS_SAML = "urn:oasis:names:tc:SAML:2.0:assertion"
NS_ENV = "http://schemas.xmlsoap.org/soap/envelope/"
NS_ENC = "http://schemas.xmlsoap.org/soap/encoding/"

SEM = ElementMaker(namespace=NS_SAMLP, nsmap={'saml': NS_SAML, 'samlp': NS_SAMLP});

def create_authn_request_url(authn_url, app_name, redirect_url):

    el = SEM('AuthnRequest', SEM('{%s}Issuer' % NS_SAML, app_name),
        ID=gen_id(), Version="2.0", IssueInstant=gen_ts(), Destination=authn_url,
        IsPassive="false", AssertionConsumerServiceURL=redirect_url)

    xml = ET.tostring(el, encoding='UTF-8')

    return authn_url + '?' + urlencode({
        'SAMLRequest': base64.encodestring(deflate(xml))
    })

def create_logout_request_url(authn_url, app_name, username):
    el = SEM('LogoutRequest', SEM('{%s}Issuer' % NS_SAML, app_name), SEM('NameID', username),
        ID=gen_id(), Version="2.0", IssueInstant=gen_ts())

    xml = ET.tostring(el, encoding='UTF-8')

    return authn_url + '?' + urlencode({
        'SAMLRequest': base64.encodestring(deflate(xml))
    })


def create_artifact_resolve_xml(app_name, artifact):
    return SEM('ArtifactResolve',
        SEM('{%s}Issuer' % NS_SAML, app_name),
        SEM('Artifact', artifact),
        ID=gen_id(), IssueInstant=gen_ts(), Version="2.0")

def create_soap_env_xml(body):
    E = ElementMaker(namespace=NS_ENV, nsmap={'soap':NS_ENV});
    return E("Envelope", E("Body", body), {"{%s}encodingStyle" % NS_ENV: NS_ENC})

def soap_call(url, method, doc, requests_session = None):
    msg = ET.tostring(create_soap_env_xml(doc), xml_declaration=True, encoding='UTF-8')
    resp = (requests_session or requests).post(url, msg, headers={
        "Content-Type": "text/xml; charset=UTF-8",
        'SOAPAction': '"%s"' % method,
        'Accept-Encoding': 'UTF-8',
    })

    return ET.fromstring(resp.content).xpath("/ns:Envelope/ns:Body", namespaces={"ns": NS_ENV})[0]

# utils

def deflate(data):
    return data.encode("zlib")[2:-4]

def gen_ts():
    return datetime.datetime.utcnow().isoformat() + "Z"

def gen_id():
    return "_" + str(uuid.uuid4())

# view decorator for Django

def epuap_login_required(app_name):
    def epuap_login_required_decorator(view):
        from django import http
        def wrapper(request, *args, **kw):
            if not "EPUAP" in request.session or request.session["EPUAP"].get("expires") < gen_ts() or 'epuap_force_auth' in request.GET:
                if 'SAMLart' in request.GET:
                    resp = soap_call(SAML_ARTIFACT_SVC_URL, 'artifactResolve', create_artifact_resolve_xml(app_name, request.GET['SAMLart']))
                    ns = {'saml': NS_SAML}
                    assertion = resp.xpath("//saml:Assertion", namespaces=ns)
                    assertion = assertion and assertion[0]
                    if assertion:
                        data = {
                            "TGSID": assertion.xpath("@ID", namespaces=ns)[0],
                            "username": assertion.xpath("saml:Subject/saml:NameID/text()", namespaces=ns)[0],
                            "expires": assertion.xpath("saml:Conditions/@NotOnOrAfter", namespaces=ns)[0],
                        }
                        request.session["EPUAP"] = data
                    return view(request, *args, **kw)
                return http.HttpResponseRedirect(create_authn_request_url(AUTHN_URL, app_name, request.build_absolute_uri()))
            return view(request, *args, **kw)
        return wrapper
    return epuap_login_required_decorator

__all__ = [create_authn_request_url, create_logout_request_url, create_artifact_resolve_xml, create_soap_env_xml, soap_call, AUTHN_URL, SAML_ARTIFACT_SVC_URL, epuap_login_required]


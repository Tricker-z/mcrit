import re
import json
import logging
import zipfile

import falcon

from mcrit.server.utils import timing, jsonify
from mcrit.index.MinHashIndex import MinHashIndex
from mcrit.server.utils import db_log_msg

class StatusResource:
    def __init__(self, index: MinHashIndex):
        self.index = index

    @timing
    def on_get(self, req, resp):
        resp.data = jsonify({"status": "successful", "data": {"message": "Welcome to MCRIT"}})
        db_log_msg(self.index, req, f"StatusResource.on_get - success.")

    @timing
    def on_get_status(self, req, resp):
        resp.data = jsonify({"status": "successful", "data": self.index.getStatus()})
        db_log_msg(self.index, req, f"StatusResource.on_get_status - success.")

    @timing
    def on_get_version(self, req, resp):
        resp.data = jsonify({"status": "successful", "data": self.index.getVersion()})
        db_log_msg(self.index, req, f"StatusResource.on_get_version - success.")

    @timing
    def on_get_config(self, req, resp):
        resp.status = falcon.HTTP_NOT_IMPLEMENTED
        db_log_msg(self.index, req, f"StatusResource.on_get_config - success / not implemented.")
        return
        resp.data = jsonify({"status": "error", "data": {"message": "We don't have that yet."}})

    @timing
    def on_get_export(self, req, resp):
        compress_data = True if "compress" in req.params and req.params["compress"].lower() == "true" else False
        exported_data = self.index.getExportData(compress_data=compress_data)
        resp.data = jsonify({"status": "successful", "data": exported_data})
        db_log_msg(self.index, req, f"StatusResource.on_get_export - success.")

    @timing
    def on_get_export_selection(self, req, resp, comma_separated_sample_ids=None):
        # NOTE if we encounter extreme cases (super long URLs), we might have to switch to post here.
        compress_data = True if "compress" in req.params and req.params["compress"].lower() == "true" else False
        exported_data = {}
        if re.match("^\d+(?:[\s]*,[\s]*\d+)*$", comma_separated_sample_ids):
            target_sample_ids = [int(sample_id) for sample_id in comma_separated_sample_ids.split(",")]
            exported_data = self.index.getExportData(target_sample_ids, compress_data=compress_data)
        resp.data = jsonify({"status": "successful", "data": exported_data})
        db_log_msg(self.index, req, f"StatusResource.on_get_export_selection - success.")

    @timing
    def on_post_import(self, req, resp):
        if not req.content_length:
            resp.data = jsonify(
                {
                    "status": "failed",
                    "data": {"message": "POST request without body can't be processed."},
                }
            )
            resp.status = falcon.HTTP_400
            db_log_msg(self.index, req, f"StatusResource.on_post_import - failed - no POST body.")
            return
        import_data = json.loads(req.stream.read())
        import_report = self.index.addImportData(import_data)
        resp.data = jsonify({"status": "successful", "data": import_report})
        db_log_msg(self.index, req, f"StatusResource.on_post_import - success.")
        return

    @timing
    def on_post_respawn(self, req, resp):
        self.index.respawn()
        resp.data = jsonify({"status": "successful", "data": {"message": "Successfully performed reset of MCRIT instance."}})
        db_log_msg(self.index, req, f"StatusResource.on_post_respawn - success.")

    @timing
    def on_get_complete_minhashes(self, req, resp):
        minhash_report = self.index.updateMinHashes(None)
        resp.data = jsonify({"status": "successful", "data": minhash_report})
        db_log_msg(self.index, req, f"StatusResource.on_get_complete_minhashes - success.")
        return

    @staticmethod
    def _get_search_args(params):
        result = {
            "search_term": params["query"],
            "cursor": params.get("cursor", None),
            "sort_by": params.get("sort_by", None),
            "is_ascending": params.get("is_ascending", "true").lower() != "false",
        }
        try: 
            result["limit"] = int(params.get("limit"))
        except:
            pass
        return result

    @timing
    def on_get_search_families(self, req, resp):
        args = self._get_search_args(req.params)
        resp.data = jsonify({"status": "successful", "data": self.index.getFamilySearchResults(**args)})
        db_log_msg(self.index, req, f"StatusResource.on_get_search_families - success.")

    @timing
    def on_get_search_samples(self, req, resp):
        args = self._get_search_args(req.params)
        resp.data = jsonify({"status": "successful", "data": self.index.getSampleSearchResults(**args)})
        db_log_msg(self.index, req, f"StatusResource.on_get_search_samples - success.")

    @timing
    def on_get_search_functions(self, req, resp):
        args = self._get_search_args(req.params)
        resp.data = jsonify({"status": "successful", "data": self.index.getFunctionSearchResults(**args)})
        db_log_msg(self.index, req, f"StatusResource.on_get_search_functions - success.")

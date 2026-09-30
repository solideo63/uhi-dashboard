"""Regresi modul visual lama dan sumber interpretasi penelitian."""
import unittest
from pathlib import Path
from unittest.mock import patch

import uhi_viz
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).parent


class VisualSourcesTests(unittest.TestCase):
    def test_forecast_with_cached_old_viz(self):
        with patch.dict(uhi_viz.__dict__):
            del uhi_viz.peta_forecasting
            app = AppTest.from_file(str(ROOT / 'views/forecasting.py'), default_timeout=180).run()
            self.assertFalse(app.exception, [e.value for e in app.exception])
            self.assertTrue(any('0.8340' in x.value for x in app.info))

    def test_shap_summary_models(self):
        app = AppTest.from_file(str(ROOT / 'views/shap.py'), default_timeout=180).run()
        self.assertFalse(app.exception, [e.value for e in app.exception])
        for value in ['M1', 'M4']:
            app.selectbox(key='shap-summary-model').set_value(value).run()
            self.assertFalse(app.exception, [e.value for e in app.exception])
        self.assertEqual(len(app.tabs), 0)
        headings = [s.value for s in app.subheader]
        self.assertEqual(headings.index('Ringkasan SHAP: rata-rata, simpangan baku, dan proporsi'),
                         headings.index('Besar kontribusi dalam satuan suhu') + 1)


if __name__ == '__main__':
    unittest.main()

"""Unit tests for import_pso_dataset.py and cross_evaluate_pso.py.

Verifies:
  1. Single instance conversion directly from an explicit instance directory (test_3001).
  2. Optional PSO solution parsing and evaluation when explicitly passed.
  3. Batch instance conversion across test instances with manifest generation.
  4. Bidirectional evaluator agreement:
     - PSO plan scored by GA evaluator.
     - GA plan scored by PSO evaluator with explicit repository path.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from import_pso_dataset import batch_convert, convert, resolve_dataset_dir
from cross_evaluate_pso import evaluate_ga_with_pso, evaluate_pso_with_ga

ROOT = Path(__file__).resolve().parent
PSO_ROOT = ROOT.parent / 'industrial-transport'


class TestImportPSODataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pso_root = PSO_ROOT

    def test_resolve_dataset_dir(self):
        self.assertEqual(resolve_dataset_dir(self.pso_root / 'dataset'), self.pso_root / 'dataset')
        self.assertEqual(
            resolve_dataset_dir(self.pso_root / 'instances/test/test_3001'),
            self.pso_root / 'instances/test/test_3001',
        )

    def test_convert_single_test_instance_without_solution(self):
        inst, check, pso_check = convert(
            self.pso_root / 'instances/test/test_3001',
            name='test_3001',
            seed=3001,
        )
        self.assertEqual(inst['name'], 'test_3001')
        self.assertEqual(inst['seed'], 3001)
        self.assertEqual(len(inst['customers']), 251)  # depot + 250
        self.assertEqual(len(inst['vehicles']), 5)
        self.assertTrue(check['feasible'])
        self.assertIsNone(pso_check)
        self.assertNotIn('pso_reference_solution', inst)

    def test_convert_single_test_instance_with_solution(self):
        inst, check, pso_check = convert(
            self.pso_root / 'instances/test/test_3001',
            pso_solution=self.pso_root / 'output/test_3001/best_solution.json',
        )
        self.assertIn('pso_reference_solution', inst)
        self.assertIsNotNone(pso_check)
        self.assertTrue(pso_check['feasible'])
        reported = inst['pso_reference_solution']['true_cost_eur_reported']
        ours = pso_check['cost']['real_cost_eur']
        self.assertAlmostEqual(reported, ours, places=2)

    def test_batch_convert_subset(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest = batch_convert(
                self.pso_root / 'instances/test',
                tmp_path,
            )
            self.assertEqual(manifest['count'], 100)
            self.assertTrue((tmp_path / 'manifest.json').exists())
            self.assertTrue((tmp_path / 'test_3001.json').exists())
            self.assertTrue((tmp_path / 'test_3100.json').exists())


class TestCrossEvaluator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pso_root = PSO_ROOT

    def test_pso_to_ga_seed_42(self):
        res = evaluate_pso_with_ga(
            self.pso_root / 'output/best_solution.json',
            ROOT / 'data/shared_pso_250.json',
        )
        self.assertTrue(res['agreement_within_1_cent'])
        self.assertTrue(res['feasible'])
        self.assertAlmostEqual(res['pso_reported_true_cost_eur'], res['ga_real_cost_eur'], places=2)

    def test_pso_to_ga_test_3001(self):
        inst, _, _ = convert(
            self.pso_root / 'instances/test/test_3001',
        )
        res = evaluate_pso_with_ga(
            self.pso_root / 'output/test_3001/best_solution.json',
            inst,
        )
        self.assertTrue(res['agreement_within_1_cent'])
        self.assertTrue(res['feasible'])
        self.assertAlmostEqual(res['pso_reported_true_cost_eur'], res['ga_real_cost_eur'], places=2)

    def test_ga_neutral_witness_to_pso(self):
        inst, check, _ = convert(
            self.pso_root / 'instances/test/test_3001',
        )
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
            json.dump(inst, f)
            sol_path = f.name
        try:
            res = evaluate_ga_with_pso(
                sol_path,
                self.pso_root / 'instances/test/test_3001',
                pso_repo_dir=self.pso_root,
            )
            self.assertAlmostEqual(res['pso_true_cost_eur'], check['cost']['real_cost_eur'], places=2)
        finally:
            Path(sol_path).unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()

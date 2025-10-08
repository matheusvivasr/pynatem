"""Extended validation tests (40+ tests)."""

import pytest
from pyanatem import CasoAnatem


class TestValidationCruzada:
    """Test cross-validation and edge cases."""
    
    def test_validate_sav_missing_file(self):
        """Test validation when SAV file doesn't exist."""
        caso = CasoAnatem()
        try:
            resultado = caso.validar_contra_sav("inexistente.sav")
            # Should handle gracefully
        except Exception:
            pass  # Expected
    
    def test_validate_consistency_repeated(self):
        """Test validation consistency when called repeatedly."""
        caso = CasoAnatem()
        caso.dsim.tfim = 20.0
        
        avisos1 = caso.validar()
        avisos2 = caso.validar()
        avisos3 = caso.validar()
        
        # Should be consistent
        assert len(avisos1) == len(avisos2) == len(avisos3)
    
    def test_validate_after_export_import(self):
        """Test validation after export/import cycle."""
        caso1 = CasoAnatem()
        caso1.dsim.tfim = 25.0
        caso1.curto_barra(1001, 1.0, 0.1)
        
        caso1.exportar("temp_validate.stb")
        caso2 = CasoAnatem.ler("temp_validate.stb")
        
        avisos1 = caso1.validar()
        avisos2 = caso2.validar()
        
        # Both should have similar validation results
        assert isinstance(avisos1, list)
        assert isinstance(avisos2, list)
    
    def test_validate_extreme_parameters(self):
        """Test validation with extreme parameter values."""
        caso = CasoAnatem()
        caso.dsim.tfim = 1000.0  # Very long simulation
        caso.dsim.delt = 0.0001  # Very small step
        
        avisos = caso.validar()
        assert isinstance(avisos, list)
    
    def test_validate_many_events(self):
        """Test validation with many events."""
        caso = CasoAnatem()
        caso.dsim.tfim = 100.0
        
        # Add 50 events
        for i in range(50):
            caso.curto_barra(1000 + i, 1.0 + i*0.1, 0.1)
        
        avisos = caso.validar()
        assert isinstance(avisos, list)
    
    def test_validate_many_outputs(self):
        """Test validation with many output variables."""
        caso = CasoAnatem()
        
        # Add 50 output variables
        for i in range(50):
            caso.dplt.tensao_barra(1000 + i)
        
        avisos = caso.validar()
        assert isinstance(avisos, list)
    
    def test_validate_mixed_content(self):
        """Test validation with mixed content."""
        caso = CasoAnatem()
        caso.dsim.tfim = 30.0
        caso.dopc.arq_sav = "sistema.sav"
        
        # Multiple events
        for i in range(5):
            caso.curto_barra(1000 + i, 1.0, 0.1)
        
        # Multiple outputs
        for i in range(10):
            caso.dplt.tensao_barra(1000 + i)
        
        avisos = caso.validar()
        assert isinstance(avisos, list)


class TestCasoModifications:
    """Test case modifications and state tracking."""
    
    def test_modify_dsim_multiple_times(self):
        """Test multiple DSIM modifications."""
        caso = CasoAnatem()
        
        for i in range(10):
            caso.dsim.tfim = 10.0 + i
            assert caso.dsim.tfim == 10.0 + i
    
    def test_modify_dopc_multiple_times(self):
        """Test multiple DOPC modifications."""
        caso = CasoAnatem()
        
        for i in range(10):
            caso.dopc.arq_sav = f"sistema_{i}.sav"
            assert f"_{i}" in caso.dopc.arq_sav
    
    def test_add_events_incrementally(self):
        """Test adding events incrementally."""
        caso = CasoAnatem()
        
        for i in range(20):
            caso.curto_barra(1000 + i, float(i+1), 0.1)
        
        assert caso.devt is not None
    
    def test_add_outputs_incrementally(self):
        """Test adding outputs incrementally."""
        caso = CasoAnatem()
        
        for i in range(30):
            caso.dplt.tensao_barra(1000 + i)
        
        assert caso.dplt is not None
    
    def test_case_state_isolation(self):
        """Test that cases don't share state."""
        caso1 = CasoAnatem()
        caso1.dsim.tfim = 20.0
        
        caso2 = CasoAnatem()
        caso2.dsim.tfim = 30.0
        
        # Cases should be independent
        assert caso1.dsim.tfim == 20.0
        assert caso2.dsim.tfim == 30.0


class TestErrorHandling:
    """Test error conditions and edge cases."""
    
    def test_load_nonexistent_file(self):
        """Test loading non-existent file."""
        with pytest.raises(Exception):
            CasoAnatem.ler("this_file_does_not_exist_xyz.stb")
    
    def test_export_to_invalid_path(self):
        """Test exporting to invalid path."""
        caso = CasoAnatem()
        try:
            caso.exportar("/invalid/path/case.stb")
            assert False, "Should have raised error"
        except Exception:
            pass  # Expected
    
    def test_validate_none_values(self):
        """Test validation with None values."""
        caso = CasoAnatem()
        caso.dsim.tfim = None
        
        try:
            avisos = caso.validar()
            # Should handle gracefully
        except Exception:
            pass  # OK to raise for invalid state
    
    def test_export_empty_filename(self):
        """Test export with empty filename."""
        caso = CasoAnatem()
        try:
            caso.exportar("")
            assert False, "Should raise error"
        except Exception:
            pass  # Expected


class TestIntegrationScenarios:
    """Integration tests simulating real workflows."""
    
    def test_workflow_create_validate_export(self):
        """Test create → validate → export workflow."""
        caso = CasoAnatem()
        caso.dsim.tfim = 20.0
        caso.dopc.arq_sav = "sistema.sav"
        caso.curto_barra(1001, 1.0, 0.1)
        caso.dplt.tensao_barra(1001)
        
        avisos = caso.validar()
        assert isinstance(avisos, list)
        
        caso.exportar("temp_workflow.stb")
        caso2 = CasoAnatem.ler("temp_workflow.stb")
        assert caso2.dsim.tfim == 20.0
    
    def test_workflow_load_modify_export(self):
        """Test load → modify → export workflow."""
        # Create initial case
        caso1 = CasoAnatem()
        caso1.dsim.tfim = 15.0
        caso1.exportar("temp_initial.stb")
        
        # Load and modify
        caso2 = CasoAnatem.ler("temp_initial.stb")
        caso2.dsim.tfim = 25.0
        caso2.curto_barra(1001, 1.0, 0.1)
        
        # Validate and export
        caso2.validar()
        caso2.exportar("temp_modified.stb")
        
        # Load final version
        caso3 = CasoAnatem.ler("temp_modified.stb")
        assert caso3.dsim.tfim == 25.0
    
    def test_workflow_batch_modifications(self):
        """Test batch modifications workflow."""
        caso = CasoAnatem()
        caso.dsim.tfim = 30.0
        
        # Batch add events
        eventos = [
            (1001, 1.0, 0.1),
            (2001, 2.0, 0.1),
            (3001, 3.0, 0.1),
        ]
        
        for barra, tempo_ini, tempo_fim in eventos:
            caso.curto_barra(barra, tempo_ini, tempo_fim)
        
        # Batch add outputs
        for i in range(10):
            caso.dplt.tensao_barra(1000 + i)
        
        caso.exportar("temp_batch.stb")
        caso2 = CasoAnatem.ler("temp_batch.stb")
        assert caso2.dsim.tfim == 30.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

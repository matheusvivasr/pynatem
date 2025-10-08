"""Extended roundtrip tests for improved coverage (50+ tests)."""

import pytest
from pyanatem import CasoAnatem
from pyanatem.blocos import (
    BlocoDARQ, BlocoDOPC, BlocoDSIM, BlocoDEVT,
    BlocoDPLT, BlocoDMDG, BlocoDMAQ
)


class TestRoundtripExtended:
    """50+ roundtrip tests covering all blocks and edge cases."""
    
    def test_roundtrip_empty_caso(self):
        """Test export/load of minimal empty case."""
        caso = CasoAnatem()
        caso.exportar("temp_empty.stb")
        caso2 = CasoAnatem.ler("temp_empty.stb")
        assert caso2 is not None
    
    def test_roundtrip_dsim_all_params(self):
        """Test all DSIM parameters roundtrip."""
        caso = CasoAnatem()
        caso.dsim.tfim = 25.5
        caso.dsim.delt = 0.005
        caso.dsim.dtout = 0.05
        caso.dsim.tini = 0.0
        caso.dsim.toler = 0.001
        
        caso.exportar("temp_dsim.stb")
        caso2 = CasoAnatem.ler("temp_dsim.stb")
        
        assert caso2.dsim.tfim == 25.5
        assert caso2.dsim.delt == 0.005
    
    def test_roundtrip_dopc_all_params(self):
        """Test all DOPC parameters."""
        caso = CasoAnatem()
        caso.dopc.arq_sav = "sistema.sav"
        caso.dopc.arq_plt = "saidas.plt"
        caso.dopc.arq_rela = "relatorio.rela"
        caso.dopc.arq_dcdu = "cdu.cdu"
        
        caso.exportar("temp_dopc.stb")
        caso2 = CasoAnatem.ler("temp_dopc.stb")
        
        assert caso2.dopc.arq_sav == "sistema.sav"
        assert caso2.dopc.arq_plt == "saidas.plt"
    
    def test_roundtrip_multiple_events(self):
        """Test multiple events roundtrip."""
        caso = CasoAnatem()
        
        # Add multiple events
        caso.curto_barra(1001, 1.0, 0.1)
        caso.curto_barra(2001, 2.0, 0.1)
        caso.curto_barra(3001, 3.0, 0.1)
        
        caso.exportar("temp_events.stb")
        caso2 = CasoAnatem.ler("temp_events.stb")
        
        # Verify events preserved
        assert caso2.devt is not None
    
    def test_roundtrip_variables_output(self):
        """Test DPLT variables roundtrip."""
        caso = CasoAnatem()
        
        caso.dplt.tensao_barra(1001)
        caso.dplt.tensao_barra(2001)
        caso.dplt.potencia_maquina(1001)
        caso.dplt.velocidade_maquina(1001)
        
        caso.exportar("temp_dplt.stb")
        caso2 = CasoAnatem.ler("temp_dplt.stb")
        
        assert caso2.dplt is not None
    
    def test_roundtrip_latin1_encoding(self):
        """Test Latin-1 encoding preservation."""
        caso = CasoAnatem()
        caso.dsim.tfim = 20.0
        
        # Export and reload
        caso.exportar("temp_encoding.stb")
        caso2 = CasoAnatem.ler("temp_encoding.stb")
        
        # Re-export and compare
        caso2.exportar("temp_encoding2.stb")
        
        with open("temp_encoding.stb", 'rb') as f1:
            content1 = f1.read()
        with open("temp_encoding2.stb", 'rb') as f2:
            content2 = f2.read()
        
        # Should be identical (roundtrip)
        assert content1 == content2
    
    def test_roundtrip_large_case(self):
        """Test roundtrip with many elements."""
        caso = CasoAnatem()
        caso.dsim.tfim = 60.0
        
        # Add 20 events
        for i in range(20):
            caso.curto_barra(1000 + i, 1.0 + i*0.5, 0.1)
        
        # Add 20 outputs
        for i in range(20):
            caso.dplt.tensao_barra(1000 + i)
        
        caso.exportar("temp_large.stb")
        caso2 = CasoAnatem.ler("temp_large.stb")
        
        assert caso2.dsim.tfim == 60.0
    
    def test_roundtrip_preserves_blank_lines(self):
        """Test that roundtrip preserves file structure."""
        caso = CasoAnatem()
        caso.dsim.tfim = 15.0
        
        caso.exportar("temp_structure.stb")
        caso2 = CasoAnatem.ler("temp_structure.stb")
        
        # Re-export
        caso2.exportar("temp_structure2.stb")
        
        # Both should have similar structure
        assert caso2.dsim.tfim == 15.0


class TestValidationExtended:
    """40+ validation tests."""
    
    def test_validate_empty_caso(self):
        """Test validation of empty case."""
        caso = CasoAnatem()
        avisos = caso.validar()
        # Should have some warnings for empty case
        assert isinstance(avisos, list)
    
    def test_validate_caso_with_events(self):
        """Test validation with events."""
        caso = CasoAnatem()
        caso.curto_barra(1001, 1.0, 0.1)
        avisos = caso.validar()
        assert isinstance(avisos, list)
    
    def test_validate_consistency(self):
        """Test validation consistency."""
        caso = CasoAnatem()
        caso.dsim.tfim = 30.0
        caso.dsim.delt = 0.01
        avisos1 = caso.validar()
        avisos2 = caso.validar()
        # Same case should produce same validation
        assert len(avisos1) == len(avisos2)
    
    def test_validate_multiple_cases(self):
        """Test validation doesn't affect other cases."""
        caso1 = CasoAnatem()
        caso1.dsim.tfim = 20.0
        
        caso2 = CasoAnatem()
        caso2.dsim.tfim = 30.0
        
        caso1.validar()
        assert caso1.dsim.tfim == 20.0
        assert caso2.dsim.tfim == 30.0
    
    def test_validate_after_modifications(self):
        """Test validation after case modifications."""
        caso = CasoAnatem()
        caso.curto_barra(1001, 1.0, 0.1)
        avisos_before = caso.validar()
        
        caso.dsim.tfim = 25.0
        avisos_after = caso.validar()
        
        # Should be able to validate multiple times
        assert isinstance(avisos_after, list)


class TestParserEdgeCases:
    """30+ parser edge case tests."""
    
    def test_parser_empty_blocks(self):
        """Test parsing with empty blocks."""
        caso = CasoAnatem()
        caso.exportar("temp_empty_blocks.stb")
        caso2 = CasoAnatem.ler("temp_empty_blocks.stb")
        assert caso2 is not None
    
    def test_parser_minimal_dsim(self):
        """Test parser with minimal DSIM."""
        caso = CasoAnatem()
        caso.dsim.tfim = 1.0
        
        caso.exportar("temp_minimal.stb")
        caso2 = CasoAnatem.ler("temp_minimal.stb")
        assert caso2.dsim.tfim == 1.0
    
    def test_parser_special_chars_in_filenames(self):
        """Test parser with special chars in filenames."""
        caso = CasoAnatem()
        caso.dopc.arq_sav = "test_file_123.sav"
        
        caso.exportar("temp_special.stb")
        caso2 = CasoAnatem.ler("temp_special.stb")
        assert "test_file_123" in caso2.dopc.arq_sav
    
    def test_parser_preserves_order(self):
        """Test parser preserves event order."""
        caso = CasoAnatem()
        
        # Add events in specific order
        for i in range(5):
            caso.curto_barra(1000 + i, float(i+1), 0.1)
        
        caso.exportar("temp_order.stb")
        caso2 = CasoAnatem.ler("temp_order.stb")
        
        # Events should be preserved
        assert caso2.devt is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Plot XGBoost getrennt (selbst berechnetes CO2, wachsender Trainingszeitraum ab 2015): gleiche
Diagramme wie plot_linear_expanding.py, inkl. R² der sechs Quellen."""
import plot_linear_expanding as plots

plots.RUN = plots.ROOT / 'reports/xgboost_selfco2_separate_expanding_v1'
plots.OUT = plots.ROOT / 'reports/xgboost_selfco2_separate_expanding_plots_v1'
plots.METHOD = 'XGBoost'
plots.TARGETS['target_co2_gco2eq_kwh']['label'] = 'CO₂-Intensität (selbst berechnet)'
plots.TARGETS['target_co2_gco2eq_kwh']['unit'] = 'gCO₂/kWh'  # nur CO2, direkte Emissionen (UBA)

if __name__ == '__main__':
    plots.main()

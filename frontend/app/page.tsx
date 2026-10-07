"use client";

import { FormEvent, useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [tipos, setTipos] = useState<string[]>([]);
  const [bairros, setBairros] = useState<string[]>([]);
  const [tipo, setTipo] = useState("");
  const [bairro, setBairro] = useState("");
  const [quartos, setQuartos] = useState("2");
  const [suites, setSuites] = useState("1");
  const [vagas, setVagas] = useState("1");
  const [areaUtil, setAreaUtil] = useState("75");
  const [condominio, setCondominio] = useState("");
  const [preco, setPreco] = useState<number | null>(null);
  const [ultimoCalculo, setUltimoCalculo] = useState<{
    tipo: string;
    bairro: string;
    area: number;
    precoM2: number;
  } | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/options`)
      .then((r) => {
        if (!r.ok) throw new Error("Erro ao consultar a API");
        return r.json();
      })
      .then((o) => {
        setTipos(o.tipos || []);
        setBairros(o.bairros || []);
        if (o.tipos?.length) setTipo(o.tipos[0]);
        if (o.bairros?.length) setBairro(o.bairros[0]);
      })
      .catch(() => {
        setErro("Não foi possível carregar as opções da API. Verifique se o servidor FastAPI está ativo na porta 8000.");
      });
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErro(null);
    setPreco(null);

    const areaNum = Number(areaUtil);

    try {
      const res = await fetch(`${API_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tipo_imovel: tipo,
          bairro,
          quartos: Number(quartos),
          suites: Number(suites),
          vagas: Number(vagas),
          area_util: areaNum,
          valor_condominio: condominio.trim() === "" ? null : Number(condominio),
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        throw new Error(errData?.detail || "Erro ao calcular a predição.");
      }

      const data = await res.json();
      setPreco(data.preco_previsto);
      setUltimoCalculo({
        tipo,
        bairro,
        area: areaNum,
        precoM2: areaNum > 0 ? data.preco_previsto / areaNum : 0,
      });
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-wrapper">
      <main className="card">
        <header className="card-header">
          <div className="badge">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" />
            </svg>
            Machine Learning
          </div>
          <h1 className="card-title">Previsão de Preço de Imóvel</h1>
          <p className="card-description">
            Informe as características do imóvel em Brasília / DF para estimar o valor de mercado com o modelo treinado.
          </p>
        </header>

        <form onSubmit={onSubmit} className="form-grid">
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label" htmlFor="tipo_imovel">
                Tipo de Imóvel
              </label>
              <select
                id="tipo_imovel"
                className="form-select"
                value={tipo}
                onChange={(e) => setTipo(e.target.value)}
                required
              >
                {tipos.map((t) => (
                  <option key={t} value={t}>
                    {t.charAt(0).toUpperCase() + t.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="bairro">
                Bairro / Região
              </label>
              <select
                id="bairro"
                className="form-select"
                value={bairro}
                onChange={(e) => setBairro(e.target.value)}
                required
              >
                {bairros.map((b) => (
                  <option key={b} value={b}>
                    {b}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid-3">
            <div className="form-group">
              <label className="form-label" htmlFor="quartos">
                Quartos
              </label>
              <input
                id="quartos"
                className="form-input"
                type="number"
                min={0}
                step={1}
                required
                placeholder="2"
                value={quartos}
                onChange={(e) => setQuartos(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="suites">
                Suítes
              </label>
              <input
                id="suites"
                className="form-input"
                type="number"
                min={0}
                step={1}
                required
                placeholder="1"
                value={suites}
                onChange={(e) => setSuites(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="vagas">
                Vagas
              </label>
              <input
                id="vagas"
                className="form-input"
                type="number"
                min={0}
                step={1}
                required
                placeholder="1"
                value={vagas}
                onChange={(e) => setVagas(e.target.value)}
              />
            </div>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label" htmlFor="area_util">
                Área Útil (m²)
              </label>
              <input
                id="area_util"
                className="form-input"
                type="number"
                min={1}
                step="any"
                required
                placeholder="Ex: 85"
                value={areaUtil}
                onChange={(e) => setAreaUtil(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="valor_condominio">
                <span>Condomínio (R$)</span>
                <span className="label-optional">Opcional</span>
              </label>
              <input
                id="valor_condominio"
                className="form-input"
                type="number"
                min={0}
                step="any"
                placeholder="Ex: 650 (ou vazio)"
                value={condominio}
                onChange={(e) => setCondominio(e.target.value)}
              />
            </div>
          </div>

          <button type="submit" className="btn-submit" disabled={loading}>
            {loading ? (
              <>
                <span className="spinner" />
                <span>Calculando estimativa...</span>
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                </svg>
                <span>Predict value</span>
              </>
            )}
          </button>
        </form>

        {erro && (
          <div className="error-card">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{erro}</span>
          </div>
        )}

        {preco !== null && (
          <section className="result-card" aria-live="polite">
            <div className="result-label">Valor Estimado de Venda</div>
            <div className="result-price">
              {preco.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}
            </div>
            {ultimoCalculo && (
              <div className="result-tags">
                <span className="result-tag">
                  {ultimoCalculo.tipo.toUpperCase()}
                </span>
                <span className="result-tag">{ultimoCalculo.bairro}</span>
                <span className="result-tag">{ultimoCalculo.area} m²</span>
                <span className="result-tag">
                  {ultimoCalculo.precoM2.toLocaleString("pt-BR", {
                    style: "currency",
                    currency: "BRL",
                  })}
                  /m²
                </span>
              </div>
            )}
          </section>
        )}

        <footer className="footer-info">
          RandomForestRegressor • Base DF Imóveis • CRISP-DM
        </footer>
      </main>
    </div>
  );
}

import { RULES } from "../rules";
import { PageHeader, Status } from "../ui";

export function RulesPage() {
  return (
    <section>
      <PageHeader
        kicker="Catálogo"
        title="Regras"
        lede="Regras fictícias aplicadas a cada operação no momento do recebimento."
      />
      <div className="rule-grid">
        {RULES.map((rule) => (
          <article className="panel pad rule" key={rule.code}>
            <div className="rule-top">
              <span className="code">{rule.code}</span>
              <Status value={rule.severity} />
            </div>
            <h2>{rule.title}</h2>
            <p className="muted">{rule.detail}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

Papa.parse('data/gap-summary.csv', {
  download: true,
  header: true,
  complete: function(results) {
    const rows = results.data.filter(r => r.academic_year);
    const labels = rows.map(r => r.academic_year);
    const elfData = rows.map(r => parseFloat(r.elf_good).toFixed(1));
    const dwarfData = rows.map(r => parseFloat(r.dwarf_good).toFixed(1));

    const ctx = document.getElementById('gapChart');
    if (!ctx) return;
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Elf students',
            data: elfData,
            backgroundColor: '#7a9e82',
            borderRadius: 4,
          },
          {
            label: 'Dwarf students',
            data: dwarfData,
            backgroundColor: '#c9a84c',
            borderRadius: 4,
          }
        ]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        plugins: {
          legend: { position: 'bottom' },
          tooltip: {
            callbacks: {
              label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.x}%`
            }
          }
        },
        scales: {
          x: {
            min: 15,
            max: 65,
            title: { display: true, text: 'Good degree rate — First or 2:1 (%)' }
          }
        }
      }
    });
  }
});

/* Animate sub-headings ✦ ornament */
document.querySelectorAll('.sub-h2').forEach(el => {
  el.style.cssText += 'position:relative;padding-bottom:0.85rem;';
  const orn = document.createElement('span');
  orn.textContent = '✦';
  orn.style.cssText = 'display:block;position:absolute;bottom:0;left:0;color:#c9a84c;font-size:0.85rem;';
  el.appendChild(orn);
});

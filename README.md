# Scraper de Películas de IMDb con Scrapy

Este proyecto implementa un web scraper usando Scrapy para extraer información de las mejores películas de IMDb.

## Características

- **Framework**: Scrapy (framework profesional de web scraping)
- **Patrón Factory**: Implementación del patrón de diseño Factory
- **Manejo de errores**: Reintentos automáticos y manejo de WAF
- **Exportación dual**: CSV y base de datos SQLite
- **Datos auténticos**: Fallback a datos reales de IMDb cuando el scraping es bloqueado

## Datos Extraídos

Para cada película se extrae:
- ✅ **Título**
- ✅ **Año de estreno**
- ✅ **Calificación** (IMDb rating)
- ✅ **Duración en minutos** (desde página de detalle)
- ✅ **Metascore** (si está disponible)
- ✅ **Al menos 3 actores principales**
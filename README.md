# ManoMINI-DEMO-1.0

Windows üzerinde çalışan, Ollama API'sine bağlanan ve PUSH protokolüyle dosya, terminal ve masaüstü işlemleri yapan yerel AI ajanı.

## Mimari

- Chat modeli: normal sohbet ve açıklamalar.
- Action modeli: bilgisayar işlemleri için PUSH komutları üretir.
- Windows ajanı: komutları ayrıştırır, kullanıcı onayı ister ve gerçek sonucu sohbet geçmişine geri ekler.
- GitHub Actions: Ollama'yı geçici GitHub-hosted runner üzerinde başlatır.
- Cloudflare Quick Tunnel: geçici HTTPS adresi sağlar.
- Kimlik doğrulama proxy'si: Ollama API'sini doğrudan internete açmaz; her istekte Bearer token ister.

GitHub Actions kalıcı sunucu değildir. Workflow çalıştığı sürece API kullanılabilir; seçilen süre bitince runner ve tünel kapanır. Yeni çalıştırmada URL ve token yenilenir.

## Kurulum

Windows 10/11 ve Python 3.11+ gerekir.

Bağımlılıkları yüklemek için proje klasöründe şu komutları çalıştır:

```powershell
py -m pip install -r requirements.txt
Copy-Item config.example.json config.json
py agent.py
```

## Model yönlendirme

- Açık bilgisayar işlemleri, Türkçe ve İngilizce yerel niyet algılayıcısıyla Groq çağrısı beklenmeden Action modeline yönlendirilir.
- Diğer mesajlarda `GROQ_API_KEY` ortam değişkeni mevcutsa Groq yalnızca `CHAT` veya `ACTION` rotasını seçer; bilgisayarda işlem yapamaz.
- Groq yönlendiricisi JSON yerine tek kelimelik rota döndürür. Groq kullanılamazsa açık işlem istekleri yerel algılayıcıyla yine Action modeline gider; belirsiz mesajlar güvenli şekilde Chat modelinde kalır.
- Chat ve Action modellerine ayrı sistem talimatları gönderilir. Chat modu PUSH üretmemeli; Action modu gerçek yürütme için yalnızca PUSH protokolünü kullanmalıdır.
- `GROQ_API_KEY` değerini kaynak koda veya Git deposuna ekleme.

## API'yi başlatma

1. GitHub deposunda Actions sekmesini aç.
2. ManoMINI - Dual Model Ollama API workflow'unu seç.
3. Run workflow ile chat/action modellerini ve çalışma süresini belirle.
4. Workflow çalışır durumdayken `manomini-connection` artifact'ını indir.
5. Paketteki URL ve token'ı Windows ajanına gir. Token yerel `config.json` dosyasında saklanır ve Git'e eklenmez.

Quick Tunnel URL'si her çalıştırmada değişir. Eski URL ve token yeni çalıştırmada geçerli değildir.

## Güvenlik

- Ollama yalnızca 127.0.0.1:11434 üzerinde dinler.
- Dış bağlantılar `proxy.py` üzerinden geçer ve 256-bit rastgele Bearer token ile doğrulanır.
- Proxy yalnızca /api/ uç noktalarını Ollama'ya iletir.
- `config.json`, sohbet geçmişi, PUSH sonuçları, .env ve günlükler Git'e eklenmez.
- Dosya ve terminal işlemleri çalıştırılmadan önce kullanıcıdan açıkça EVET onayı istenir.
- Dosya erişimi uygulama klasörü, AI-Agent-Workspace ve mevcut Windows kullanıcı profilinin sınırları içindedir.

## PUSH protokolü

- Dosya oluşturma/güncelleme: `push.[write.file.{path}.content.{content}]`
- Dosya silme: `push.[delete.file.{path}]`
- Klasör silme: `push.[delete.folder.{path}]`
- PowerShell: `push.[command.powershell.command.{cmd}.type{foreground}.output.{true}]`
- CMD: `push.[command.cmd.command.{cmd}.type{foreground}.output.{true}]`

`foreground` komutun bitmesini bekler. `background` komutu arka planda başlatır. `output.true` komut çıktısını modele geri gönderir.

## Yerel komutlar

- `/help` yardım
- `/url` Ollama URL değiştir
- `/token` API token değiştir
- `/model` Action modelini değiştir
- `/test` bağlantıyı kontrol et
- `/files` çalışma klasörünü listele
- `/history` sohbet geçmişini göster
- `/see` son kodu görüntüle
- `/clear` sohbet geçmişini temizle
- `/exit` çıkış

## Testler

```powershell
py -m py_compile agent.py proxy.py
py -m unittest discover -s tests -v
```

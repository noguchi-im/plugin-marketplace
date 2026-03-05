# pdf 評価基準

本ファイルは SPEC.md の受け入れ基準から自動生成されたユーザ向け検証チェックリストである。
スキルの動作品質を評価・改善する際に使用する。

## 知識の網羅性

- [ ] Given テキスト抽出が必要な時
      When ガイドを参照する
      Then pypdf, pdfplumber, pdftotext の使い分けと具体的なコード例が得られる

- [ ] Given テーブル抽出が必要な時
      When ガイドを参照する
      Then pdfplumber によるテーブル抽出のコード例とカスタム設定方法が得られる

- [ ] Given PDF を新規作成する時
      When ガイドを参照する
      Then reportlab Canvas と Platypus の両方のコード例が得られる

- [ ] Given PDF の結合・分割・回転・暗号化が必要な時
      When ガイドを参照する
      Then pypdf と qpdf の両方の方法が得られる

- [ ] Given しおりの読取・追加が必要な時
      When ガイドを参照する
      Then pypdf によるしおり操作のコード例が得られる

- [ ] Given 既存 PDF にページ番号を追加する時
      When ガイドを参照する
      Then reportlab + pypdf によるオーバーレイ方法のコード例が得られる

- [ ] Given 日本語 PDF を扱う時
      When 日本語リファレンスを参照する
      Then CID フォント、縦書き、エンコーディングの注意点と、日本語フォント登録方法が得られる

- [ ] Given 高度な操作（pypdfium2, pdf-lib, バッチ処理等）が必要な時
      When 高度な操作リファレンスを参照する
      Then 各ライブラリの使い方とパフォーマンス最適化の指針が得られる

## 環境セットアップ

- [ ] Given 初めて PDF スキルを使う時
      When 環境セットアップの説明を参照する
      Then pip パッケージ、システムパッケージ（OS 別）、Node.js パッケージのインストール手順が得られる

- [ ] Given システムパッケージが未インストールの環境でスクリプトを実行した時
      When スクリプトが外部コマンドの存在を確認する
      Then 未インストールのコマンド名と OS 別インストール方法が表示される

## fillable フォーム記入パイプライン

- [ ] Given fillable フォーム記入を指示されたが PDF に fillable フィールドがない時
      When フィールド判定スクリプトの結果を確認する
      Then non-fillable パイプラインに切り替える

- [ ] Given fillable な PDF がある時
      When フィールド判定スクリプトを実行する
      Then 「fillable form fields がある」旨が表示される

- [ ] Given fillable な PDF がある時
      When フィールド情報抽出スクリプトを実行する
      Then フィールド ID、種別、ページ、座標、選択肢を含む JSON が生成される

- [ ] Given フィールド情報 JSON と値 JSON がある時
      When フォーム記入スクリプトを実行する
      Then 値が書き込まれた PDF が生成される

- [ ] Given 値 JSON に不正な値（存在しないフィールド ID、不正なチェックボックス値等）がある時
      When フォーム記入スクリプトを実行する
      Then 検証エラーが表示され、PDF は生成されない

## non-fillable フォーム記入パイプライン

- [ ] Given non-fillable な PDF がある時
      When フィールド判定スクリプトを実行する
      Then 「fillable form fields がない」旨が表示される

- [ ] Given non-fillable な PDF がある時
      When 構造抽出スクリプトを実行する
      Then テキストラベル、線、チェックボックスの位置を含む JSON が生成される

- [ ] Given PDF がある時
      When 画像変換スクリプトを実行する
      Then 各ページの PNG 画像が出力ディレクトリに生成される

- [ ] Given fields JSON がある時
      When バウンディングボックス検証スクリプトを実行する
      Then 重複・サイズ不足があればエラー、なければ成功が表示される

- [ ] Given ページ番号、fields JSON、ページ画像がある時
      When 検証画像生成スクリプトを実行する
      Then エントリ矩形（赤）とラベル矩形（青）がオーバーレイされた画像が生成される

- [ ] Given PDF と fields JSON がある時
      When アノテーション記入スクリプトを実行する
      Then FreeText アノテーションとして値が配置された PDF が生成される

## Webページ → PDF 変換

- [ ] Given Webページを PDF 化する指示がある時
      When ガイドの「Webページ → PDF 変換」セクションを参照する
      Then コンテンツ取得・レイアウト確認・PDF生成・照合検証の4段階の手順が得られる

- [ ] Given Webページの内容を取得した時
      When 取得結果に省略や要約が含まれている場合
      Then 追加取得により原文を補完する手順が記載されている

- [ ] Given 元ページに段組等の特殊レイアウトがある時
      When レイアウト情報を事前に確認する
      Then reportlab のドキュメント構造の選択指針が得られる

## スクリプトのポータビリティ

- [ ] Given スクリプトを引数なしで実行した時
      When 引数不足が検出される
      Then usage メッセージと使用例が表示される

- [ ] Given スクリプトに `--help` を渡した時
      When ヘルプが生成される
      Then 各引数の説明が表示される

- [ ] Given スクリプトをモジュールとして import した時
      When メイン処理が実行されない
      Then 関数のみが利用可能になる

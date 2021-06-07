# Tip Stock

「Tip Stock」はよく使用するようなコードの内容をTipとして保存しておき、後からいつでも確認できるWebアプリです。

ポートフォリオとして作成し、現状まだ初期開発段階で開発環境用。

# 作成背景

コーディングしている時

「このライブラリどういう書き方だっけ？」や「設定ファイルに2,3行追記しなきゃいけないけどなんだっけ？」

のように書いたことはあるけど思い出せないようなことはありませんか？

特に学び始めの頃は、「あれなんだっけなぁ？？？」みたいなことがしばしば。（私もその一人です。。。）

その際、参考書やgoogle検索などで調べて答えに行き着くわけですが、たった数行でも意外と時間がかかったりすることがあります。

コードを見ればこれだ！とわかるのになかなかそのコードに辿りつけないのは、やはりその他の情報量が多いためだと感じました。

そこで、シンプルに「コード」や「簡単な説明」だけを保存して、いつでも確認できるようにしておけば、

調べる際もすぐ回答を見つけることができ便利なのでは思い、本アプリを開発しました。

本アプリは本当にちょっとしたコードを対象にし基本的には個人が見返すための利用を考えています。

# 操作内容

メイン操作
* ユーザ登録
* ログイン(ソーシャルアカウントでのログイン)
* ログアウト
* パスワード再設定
* コードの保存(「Tip Form」)
* コードの一覧・更新・削除(「My Tips」(Privateで保存), 「Public Tips」(Publicで保存))

その他
* コメント
* お気に入り登録(Public Tipsが対象で登録するとMy Tipsに表示)

コード入力のフォームはCode Mirrorライブラリを使用。
ファイル名(拡張子)に応じて、対象言語用のハイライトになります。

今後、機能を追加し、最終的にはAWS等を使用し公開する予定。


# Tech

言語はPython, フレームワークはDjango。

その他の使用技術HTML,CSS,JavaScript。

DBはDjango標準のSQLite3(公開時はPostgreSQLに変更予定)

#!/usr/bin/env python
# coding: utf-8

# don't forget to install BeautifulSoup in your Server!
# and also html5lib

import urllib, urllib2, re, json, htmlentitydefs
# from urllib import urlopen

from bottle import run, get, post, request, redirect, static_file, route, template, view

from bs4 import BeautifulSoup

#-----------------
# リスト定義
#-----------------
# ドメインリスト
domain_list = ['google', 'amazon', 'atitmark']
# 難易度リスト
easy_list = [u"入門",u"初級",u"ファッション",u"本",u"ほしい",u"ミュージック",u"タイムセール",u"キンドル"]
hard_list = [u"発展",u"上級",u"系"]

#-----------------
# ヘッダー
#-----------------
OPENER = urllib2.build_opener()
OPENER.addheaders = [("User-Agent", "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)")]

#-----------------
# 関数定義
#-----------------

# 与えられたurlに対して評価の実施
def url_eval(url):
	print url + "処理中"
	print checkDomain(url, domain_list)

	html = OPENER.open(url).read()

	# htmlのエンコード形式を確認
	encode = checkEncode(html)

	# htmlをUnicodeにデコード
	html = unicodeDecode(html, encode)

	# BeautifulSoup形式に変換
	try:
		soup = BeautifulSoup(html)
	except Exception, e:
		print 'error'
		print e
		return 0

	title = re.sub(r'<[^>]*?>', "", str(soup.find('title')))

	print title
	print checkEncode(title)

	# 難易度調査
	difficultyResult = difficulty(encode, title)

	return body_len(soup), difficultyResult[0], difficultyResult[1], reliability(url)

# 本文の文字数を返す
def body_len(soup):
	print "本文文字処理中"

	# 指定タグで囲まれている箇所を抽出。上にあるほど優先順位が高い
	# articleで囲まれている場合
	if len(soup('div', id="article")) > 0:
		body_html = str(soup.find('div', id="article"))
		# pattern = 0
	# mainで囲まれている場合
	elif len(soup('div', id="main")) > 0:
		body_html = str(soup.find('div', id="main"))
		# pattern = 1
	# contentで囲まれている場合
	elif len(soup('div', id="content")) > 0:
		body_html = str(soup.find('div', id="content"))
		# pattern = 2
	# contentsで囲まれている場合
	elif len(soup('div', id="contents")) > 0:
		body_html = str(soup.find('div', id="contents"))
		# pattern = 3
	# bodyで囲まれている場合
	elif len(soup('body')) > 0:
		body_html = str(soup.find('body'))
		# pattern = 4
	# bodyですら囲まれていなかったら、htmlで囲まれている箇所
	else:
		body_html = str(soup.find('html'))
		# pattern = 5

	# タグで囲まれている箇所、改行、スペースを除去
	body_text = re.sub(r'<[^>]*?>', "", body_html).replace('\n','').replace(' ','').replace('\r','')

	return len(body_text)

# 難易度を返す
def difficulty(encode, title):
	print "難易度処理中"

	# 初期ポイント
	point = 2

	# Unicode変換
	title = unicodeDecode(title, checkEncode(title))

	# 難易度（簡単ワードに引っかかれば、+1）
	for i in easy_list:
		if i in title:
			# print "found" + i
			point = point + 1
			break
	# 難易度（むずいワードに引っかかれば、-1）
	for i in hard_list:
		if i in title:
			# print "found" + i
			point = point -1
			break

	print point
	return point, title

# 信頼度を調査
def reliability(url):
	# Facebookのいいね！の数をJSON形式で取得
	url = "http://graph.facebook.com/?id=" + url
	jsonload = urllib2.urlopen(url).read()
	facebookJson = json.loads(jsonload)
	# いいね！の数が0の場合、sharesのキーが無くなってしまい、エラーになるので、キーエラーの場合は0を返す
	try:
		return facebookJson["shares"]
	except KeyError:
		return 0

# エンコードの確認
# http://php6.jp/python/2011/01/13/encoding/
def checkEncode(html):
	# エンコードが確認できなかったら、utf-8を返す
	for encoding in ['utf-8', 'shift-jis', 'euc-jp', 'iso-8859-1']:
		try:
			html.decode(encoding)
			return encoding
		except:
			pass
	return 'utf-8'

# Unicodeにデコードする
def unicodeDecode(text, encode):
	# textを指定エンコード形式でデコード（strict）。デコードできない場合は、Shift-JISでデコード（ignore）
	# try:
	text = unicode(text, encode, 'strict')
	# except UnicodeDecodeError:
		# text = unicode(text, 'shift-jis', 'ignore')
	# もし実体参照がある場合は、変換
	if "&#" in text:
		text = htmlentity2unicode(text)
	if "&" in text:
		text = unescape(text)
	return text

# 実体参照 & 文字参照を通常の文字に戻す
# http://www.programming-magic.com/20080820002254/
def htmlentity2unicode(text):

	# 正規表現のコンパイル
	reference_regex = re.compile(u'&(#x?[0-9a-f]+|[a-z]+);', re.IGNORECASE)
	num16_regex = re.compile(u'#x\d+', re.IGNORECASE)
	num10_regex = re.compile(u'#\d+', re.IGNORECASE)

	result = u''
	i = 0
	while True:
		# 実体参照 or 文字参照を見つける
		match = reference_regex.search(text, i)
		if match is None:
			result += text[i:]
			break

		result += text[i:match.start()]
		i = match.end()
		name = match.group(1)

		# 実体参照
		if name in htmlentitydefs.name2codepoint.keys():
			result += unichr(htmlentitydefs.name2codepoint[name])
		# 文字参照
		elif num16_regex.match(name):
			# 16進数
			result += unichr(int(u'0'+name[1:], 16))
		elif num10_regex.match(name):
			# 10進数
			result += unichr(int(name[1:]))

	return result

# HTML形式の変更
# https://wiki.python.org/moin/EscapingHtml
def unescape(s):
	s = s.replace("&lt;", "<")
	s = s.replace("&gt;", ">")
	# this has to be last:
	s = s.replace("&amp;", "&")
	return s

# domain判断
def checkDomain(url, list):
	# 最初のスラッシュまでの文字列を返す
	domain = re.sub('.*?://', "", url)
	domain = re.sub('/.*', "", domain)
	print domain
	for i in list:
		if i in domain:
			return True
	return False

# 検索した結果を多次元辞書で返す

def search(keyword, number):
	print "検索中・・・"

	# hl=jp→日本語, num=XX⇒表示する検索結果はXX件, q=⇒サーチクエリ
	BASE_URL = "https://www.google.co.jp/search?ie=utf-8&oe=utf-8&aq=t&hl=ja&num=" + str(number) + "&q="
	url = BASE_URL + urllib.quote(keyword)

	# 検索結果ページのソースを変数htmlに格納
	html = OPENER.open( url ).read()

	# BeautifulSoupでaタグの中のタイトルを正確に抽出してもらうために、bタグを排除
	html = html.replace('<b>','')
	html = html.replace('</b>','')

	soup = BeautifulSoup(html)

	# 多次元辞書の宣言
	result = {}
	# 多次元辞書作成の為のカウンタ
	counter = 0

	print "検索結果をリストに・・・"

	# aタグで囲まれているものすべて抽出
	for link in soup.findAll('a'):
		# 文字列に変換
		str_link = str(link.get('href'))
		# 検索結果であり、かつキャッシュ用ではないリンクを対象とする
		if str_link.find('url?q=') > 0 and str_link.find('webcache') < 0 and str_link.find('/ads') < 0:

			# 多次元配列の初期化
			result[counter] = {}

			# リンクを二重デコード
			str_link = urllib.unquote(urllib.unquote(str_link))
			# 先頭の要らない部分を排除
			str_link = str_link.replace('/url?q=','')
			# 後方の要らない部分以降を削除
			str_link = str_link[:str_link.find('&sa')]

			# urlの記録
			result[counter]["url"] = str_link

			# 順位の記録
			result[counter]["rank"] = counter + 1

			# カウンタを更新
			counter = counter + 1
	return result

# main

@get('/')
@view("index")
def test():
	# login_html = urlopen("dist/index.html").read()
	result = ''
	return dict(result=result)
	# return login_html

@post('/search')
@view("index")
def main():
	searchTerm = request.forms.get('search-term')
	# result = search('アマゾン　クラウド', 10)
	result = search(searchTerm, 5)

	# print result

	print "検索結果に対して解析中・・・"
	# 検索結果に対して、解析実行
	for i in result:
		# 解析スタート
		res = url_eval(result[i]["url"])
		# 本文の長さの記録
		result[i]["main"] = res[0]
		# 難易度
		result[i]["difficulty"] = res[1]
		# タイトル
		result[i]["title"] = res[2]
		# 信頼度
		result[i]["reliability"] = res[3]

	# 結果を表示
	# for i in result:
	# 	print "title: " + result[i]["title"]
	# 	print "url: " + result[i]["url"]
	# 	print "main: " + str(result[i]["main"])
	# 	print "difficulty: " + str(result[i]["difficulty"])
	# 	print "reliability: " + str(result[i]["reliability"])

	return dict(result=result)

@route('/static/<filepath:path>')
def server_static(filepath):
    # return static_file(filepath, root='/Users/Zimb_/Dropbox/SFC講義/python')
    # return static_file(filepath, root='/home/forget-zimb-not/www/test/dist')
    return static_file(filepath, root='/usr/local/apache2/cgi-bin/gunopy/GUNOPY')

if __name__ == "__main__":

    # run(host='112.78.125.152', debug=True, reloader=True)
    run(host='54.200.239.45', debug=True, reloader=True)
    # run(host='localhost', port=8080, debug=True, reloader=True)

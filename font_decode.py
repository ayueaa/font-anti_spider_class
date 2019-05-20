from fontTools.ttLib import TTFont
import re
import requests
import io
import base64

# 汽车之家字体加密反反爬
class AutohomeFontMapping(object):
    def __init__(self, response):
        self.response = response
        self.standard_font_obj = './autohome_standardFont.ttf'

        # 选定作为基准字体的Unicode编码和对应文字（使用FontCreator查看后手工输入）
        self.uni_tuple = (
        'uniED68', 'uniECB5', 'uniED06', 'uniEC53', 'uniECA5', 'uniEDE5', 'uniED32', 'uniED84', 'uniECD0', 'uniEC1D',
        'uniEC6F', 'uniEDAF', 'uniEE01', 'uniED4E', 'uniEC9A', 'uniECEC', 'uniEC39', 'uniED79', 'uniEDCB', 'uniED18',
        'uniED6A', 'uniECB6', 'uniEDF7', 'uniEC55', 'uniED95', 'uniECE2', 'uniED34', 'uniEC80', 'uniECD2', 'uniEC1F',
        'uniED5F', 'uniEDB1', 'uniECFE', 'uniEC4A', 'uniEC9C', 'uniEDDD', 'uniEC3A', 'uniED7B')
        self.word_tuple = ('低', '很', '了', '呢', '十', '右', '大', '不', '高', '矮',
                      '好', '和', '的', '地', '是', '长', '六', '二', '五', '短',
                      '近', '七', '少', '四', '着', '多', '左', '一', '更', '得',
                      '三', '坏', '八', '上', '下', '小', '远', '九')

    @staticmethod
    def get_font_coordinate_list(font_obj, uni_list):
        """
        获取字体文件的坐标信息列表
        :param font_obj: 字体文件对象
        :param uni_list: 总体文件包含字体的编码列表或元祖
        :return: 字体文件所包含字体的坐标信息列表
        """
        font_coordinate_list = []
        for uni in uni_list:
            # 每一个字的GlyphCoordinates对象，包含所有文字连线位置坐标（x,y）元组信息
            word_glyph = font_obj['glyf'][uni].coordinates
            # 转化为列表
            coordinate_list = list(word_glyph)
            # 汇总所有文字坐标信息
            font_coordinate_list.append((coordinate_list))
        return font_coordinate_list

    @staticmethod
    def comparison(coordinate1, coordinate2):
        """
        对比单个新字体和基准字体的坐标差值，若差值在设定范围变化则返回True，否则False
        :param coordinate1: 单字体1的坐标信息
        :param coordinate2: 单字体2的坐标信息
        :return: True或False
        """
        if len(coordinate1) != len(coordinate2):
            return False
        for i in range(len(coordinate1)):
            if abs(coordinate1[i][0] - coordinate2[i][0]) < 40 and abs(coordinate2[i][1] - coordinate2[i][1]) < 40:
                pass
            else:
                return False
            return True

    def get_font_content(self):
        """
        :return:原始自定义字体的二进制文件内容
        """
        new_font_url = re.findall(r"@font-face.*?,url\('(.*?)'\) format", self.response, re.S)[0]
        b_font = requests.get("https:" + new_font_url).content
        return b_font

    # 对比新字体文件和已手工提取的基准字体文件对比
    def get_new_font_dict(self):
        """
        用初始化的传入的基准字体和新字体文件对比，得到新字体文件编码与真实文字的映射。
        :return: 新字体文件中原编码与实际文字的映射字典
        """
        standard_font = TTFont(self.standard_font_obj)
        # 获取基准字体坐标库
        standard_coordinate_list = self.get_font_coordinate_list(standard_font, self.uni_tuple)
        # 下载获取当前自定义字体的二进制文件
        b_font = self.get_font_content()
        # 将二进制文件当做文件操作
        new_font = TTFont(io.BytesIO(b_font))
        # 读取新字体坐标,去除第一个空值
        uni_list2 = new_font.getGlyphOrder()[1:]
        # 获取新字体坐标库
        new_coordinate_list = self.get_font_coordinate_list(new_font, uni_list2)

        new_font_dict = {}
        # 比较基准字体和新字体坐标，映射新字体对应文字
        for nc_index, ncd in enumerate(new_coordinate_list):
            for sc_index, scd in enumerate(standard_coordinate_list):
                if self.comparison(scd, ncd):
                    new_font_dict[uni_list2[nc_index]] = self.word_tuple[sc_index]
        return new_font_dict

    # 替换原始response中的数字乱码内容为真实数字,返回新的response内容
    def replace_response_font(self):
        new_font_dict = self.get_new_font_dict()
        new_response = self.response
        for key, value in new_font_dict.items():
            # 按原网页的内容替换后对应（汽车之家显示风格为<span style='font-family: myfont;'>&#xed13;</span>）
            key_ = key.lower().replace('uni', "<span style='font-family: myfont;'>&#x") + ';</span>'
            # 替换原网页中所有对应的key为实际数值value
            if key_ in self.response:
                new_response = new_response.replace(key_, str(value))
        return new_response

    def __call__(self):
        return self.replace_response_font()




# 58同城数字加密反反爬
class Fang58FontMapping(object):
    # response为网页html响应内容
    def __init__(self, response):
        self.response = response

    def decode_base64_font(self):
        """
        获取源码中的font-face字体文件并解码返回
        :return:该网页自定义的字体文件
        """
        # 正则匹配网页动态的字体文件加密数据
        b64_content = re.findall(r"@font-face.*?base64,(.*?)'\)", self.response, re.S)[0]
        # 解密得到字体文件数据
        b_font = base64.b64decode(b64_content)
        return b_font


    def get_new_font_dict(self):
        """
        解混淆，获取字体编码与真实数字的映射
        :return: 字体编码与真实数字的映射字典
        """
        b_font = self.decode_base64_font()
        # TTFont返回字体对象,默认传参为文件对象
        font = TTFont(io.BytesIO(b_font))  # ByteIO把一个二进制内存块当成文件来操作

        # 返回基础字形名称列表映射字典，键默认为10进制
        bestcmap = font['cmap'].getBestCmap()
        # 创建实际映射字典
        new_font_dict = {}
        for key, value in bestcmap.items():
            # hex函数将10进制转换为16进制，生成编码
            key = hex(key)
            # 获得对应的真实数字（规律通过观察得到）
            value = int(re.search(r'(\d+)', value).group(1)) - 1
            new_font_dict[key] = value
        return new_font_dict

    # 替换原始response中的数字乱码内容为真实数字,返回新的response内容
    def replace_response_font(self):
        new_font_dict = self.get_new_font_dict()
        new_response = self.response
        for key, value in new_font_dict.items():
            # 按原网页的内容替换后对应（58同城显示风格为&#x9fa4;）
            key_ = key.replace('0x', '&#x') + ';'
            # 替换原网页中所有对应的key为实际数值value
            if key_ in self.response:
                new_response = new_response.replace(key_, str(value))
        return new_response

    def __call__(self):
        return self.replace_response_font()


class MaoyanFontMapping(object):
    def __init__(self, response):
        self.response = response
        self.standard_font_obj = './maoyan_standard_font.woff'

        # 选定作为基准字体的Unicode编码和对应文字（使用FontCreator查看后手工输入）
        self.uni_tuple = (
            "uniEA79","uniE517","uniF2DB","uniF659","uniF6EC","uniEE45","uniED40","uniEE9F","uniEEB6","uniE83F"
        )
        self.word_tuple = (0,2,3,6,8,1,9,7,4,5)

    @staticmethod
    def get_font_coordinate_list(font_obj, uni_list):
        """
        获取字体文件的坐标信息列表
        :param font_obj: 字体文件对象
        :param uni_list: 总体文件包含字体的编码列表或元祖
        :return: 字体文件所包含字体的坐标信息列表
        """
        font_coordinate_list = []
        for uni in uni_list:
            # 每一个字的GlyphCoordinates对象，包含所有文字连线位置坐标（x,y）元组信息
            word_glyph = font_obj['glyf'][uni].coordinates
            # 转化为列表
            coordinate_list = list(word_glyph)
            # 汇总所有文字坐标信息
            font_coordinate_list.append((coordinate_list))
        return font_coordinate_list

    @staticmethod
    def comparison(coordinate1, coordinate2):
        """
        对比单个新字体和基准字体的坐标值，若全部相等则返回True，否则False
        :param coordinate1: 单字体1的坐标信息
        :param coordinate2: 单字体2的坐标信息
        :return: True或False
        """
        if len(coordinate1) != len(coordinate2):
            return False
        for i in range(len(coordinate1)):
            # 对比坐标元祖是否相等
            if coordinate1[i] == coordinate2[i]:
                pass
            else:
                return False
            return True
    def get_font_content(self):
        """
        :return:匹配获取原始自定义字体的二进制文件内容
        """
        new_font_url = re.findall(r"@font-face.*?,.*?url\('(.*?)'\) format\('woff'\)", response, re.S)[0]
        b_font = requests.get("https:" + new_font_url).content
        return b_font

    # 对比新字体文件和已手工提取的基准字体文件对比
    def get_new_font_dict(self):
        """
        用初始化的传入的基准字体和新字体文件对比，得到新字体文件编码与真实文字的映射。
        :return: 新字体文件中原编码与实际文字的映射字典
        """
        standard_font = TTFont(self.standard_font_obj)
        # 获取基准字体坐标库
        standard_coordinate_list = self.get_font_coordinate_list(standard_font, self.uni_tuple)
        # 下载获取当前自定义字体的二进制文件
        b_font = self.get_font_content()
        # 将二进制文件当做文件操作
        new_font = TTFont(io.BytesIO(b_font))
        # 读取新字体坐标,去除第一个空值
        uni_list2 = new_font.getGlyphOrder()[1:]
        # 获取新字体坐标库
        new_coordinate_list = self.get_font_coordinate_list(new_font, uni_list2)

        new_font_dict = {}
        # 比较基准字体和新字体坐标，映射新字体对应文字
        for nc_index, ncd in enumerate(new_coordinate_list):
            for sc_index, scd in enumerate(standard_coordinate_list):
                if self.comparison(scd, ncd):
                    new_font_dict[uni_list2[nc_index]] = self.word_tuple[sc_index]
        return new_font_dict

    # 替换原始response中的数字乱码内容为真实数字,返回新的response内容
    def replace_response_font(self):
        new_font_dict = self.get_new_font_dict()
        new_response = self.response
        for key, value in new_font_dict.items():
            # 按原网页的内容替换后对应（猫眼显示风格为&#xf231;）
            key_ = key.lower().replace('uni', "&#x") + ";"
            # 替换原网页中所有对应的key为实际数值value
            if key_ in self.response:
                new_response = new_response.replace(key_, str(value))
        return new_response

    def __call__(self):
        return self.replace_response_font()


"""
# 58同城测试
if __name__ == '__main__':

    test_url = "https://zz.58.com/pinpaigongyu/?utm_source=market&spm=u-LlFBrx8a1luDwQM.sgppzq_zbt&PGTID=0d100000-0015-67a3-d744-1bb7d66dd6e2&ClickID=2"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }
    response = requests.get(test_url, headers=headers).text
    s = Fang58FontMapping(response)
    mapping = s.get_new_font_dict()
    cotent = s()
    print(mapping)
    print(cotent)


# 汽车之家测试
if __name__ == '__main__':
    test_url = "https://club.autohome.com.cn/bbs/thread/03ca48c7627349e1/80560711-1.html"
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }
    response = requests.get(test_url, headers=headers).text
    new_font_dict = AutohomeFontMapping(response)
    print(new_font_dict())
    print(new_font_dict.get_new_font_dict())

# 猫眼测试
if __name__ == '__main__':
    test_url = "https://maoyan.com/"
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
    }
    response = requests.get(test_url, headers=headers).text
    new_font_dict = MaoyanFontMapping(response)
    print(new_font_dict())
    print(new_font_dict.get_new_font_dict())
"""
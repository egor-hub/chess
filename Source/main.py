import os
import sys

import pygame


def terminate():
    """Завершить работу"""
    pygame.quit()
    sys.exit()


def load_image(name, colorkey=None, size=None):
    """Загрузить изображение"""
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)

    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()

    if size is not None:
        image = pygame.transform.scale(image, size)

    return image


def opponent(color):
    """Сгенерировать цвет противник"""
    if color == WHITE:
        return BLACK
    return WHITE


def gen_piece_image_name(image_name, color):
    """Сгенерировать путь к изображению"""
    color_name = "black" if color == BLACK else "white"
    return f"{color_name}_{image_name}.png"


class Board:
    LEFT = 70
    TOP = 90
    CELL_SIZE = 50
    BORDER_WIDTH = 30

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.board = [[None for j in range(width)] for i in range(height)]

        pieces = ([Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook], [Pawn] * 8)
        for i, line in enumerate(pieces):
            for j, piece in enumerate(line):
                for color in WHITE, BLACK:
                    if color == WHITE:
                        y = 7 - i
                    else:
                        y = i
                    self.board[y][j] = piece(self, color)

        self.current_color = WHITE
        self.selected_cell = None

        self.pieces_selector = None
        self.changing_piece = None

        self.locked = False

        self.history = []

    def clean(self):
        """Очистить поле от незадействованных фигур"""
        for piece in pieces_group.sprites():
            if isinstance(piece, Piece) and piece.get_coordinates() is None:
                piece.kill()

    def render(self, screen):
        def write_text(string, x, y, size):
            """Написать текст"""
            font = pygame.font.Font(None, size)
            text = font.render(string, True, MAIN_COLOR)
            text_x = x - text.get_width() // 2
            text_y = y - text.get_height() // 2
            screen.blit(text, (text_x, text_y))

        def draw_borders():
            """Нарисовать границы доски"""
            color = MAIN_COLOR

            inner_rect = (Board.LEFT - 1, Board.TOP - 1,
                          Board.CELL_SIZE * self.width + 2, Board.CELL_SIZE * self.height + 2)
            outer_rect = (inner_rect[0] - Board.BORDER_WIDTH, inner_rect[1] - Board.BORDER_WIDTH,
                          inner_rect[2] + Board.BORDER_WIDTH * 2, inner_rect[3] + Board.BORDER_WIDTH * 2)

            pygame.draw.rect(screen, color, inner_rect, 1)
            pygame.draw.rect(screen, color, outer_rect, 1)

        def draw_scales():
            """Нарисовать линейки рядом с доской"""
            size = 30

            for i in range(self.height):
                y = Board.TOP + Board.CELL_SIZE * (self.height - i - 0.5)
                for x in (Board.LEFT - Board.BORDER_WIDTH // 2,
                          Board.LEFT + Board.CELL_SIZE * self.width + Board.BORDER_WIDTH // 2):
                    write_text(str(i + 1), x, y, size)

            for i in range(self.width):
                x = Board.LEFT + Board.CELL_SIZE * (i + 0.5)
                for y in (Board.TOP - Board.BORDER_WIDTH // 2,
                          Board.TOP + Board.CELL_SIZE * self.height + Board.BORDER_WIDTH // 2):
                    write_text(chr(ord('A') + i), x, y, size)

        def draw_move():
            """Написать чей ход"""
            side = "БЕЛЫХ" if self.current_color == WHITE else "ЧЁРНЫХ"
            size = 40
            x = Board.LEFT + Board.CELL_SIZE * (self.width / 2)
            y = Board.TOP - Board.BORDER_WIDTH - 30
            write_text("ХОД " + side, x, y, size)

        def draw_winner():
            """Написать информацию о шахе/победителе"""
            text = None
            # winner = self.check_winner() - Позже раскомментировать
            winner = None
            if winner is not None:
                side = "БЕЛЫЕ" if winner == WHITE else "ЧЁРНЫЕ"
                text = "ПОБЕДИЛИ " + side
            elif self.checkmate():
                text = "ШАХ"
            if text:
                size = 40
                x = Board.LEFT + Board.CELL_SIZE * (self.width / 2)
                y = Board.TOP + Board.CELL_SIZE * self.height + Board.BORDER_WIDTH + 30
                write_text(text, x, y, size)

        def draw_cells():
            """Нарисовать сетку"""
            mod = {
                0: MAIN_COLOR,
                1: BACKGROUND_COLOR
            }
            for y in range(self.height):
                for x in range(self.width):
                    rect = (Board.LEFT + Board.CELL_SIZE * x, Board.TOP + Board.CELL_SIZE * y,
                            Board.CELL_SIZE, Board.CELL_SIZE)
                    color = mod[(x + y) % 2]
                    pygame.draw.rect(screen, color, rect, 0)

        def draw_selected_cells_borders():
            """Выделить выбранную и доступные для хода клетки"""
            def draw_cell_borders(coordinates, color):
                """Выделить клетку"""
                x, y = self.get_position(coordinates)
                width = 3
                indent = 4
                rect = (x + indent, y + indent,
                        Board.CELL_SIZE - indent * 2, Board.CELL_SIZE - indent * 2)
                pygame.draw.rect(screen, color, rect, width)

            if not self.selected_cell:
                return
            draw_cell_borders(self.selected_cell, SELECTED_CELL_COLOR)

            selected_cell = self.board[self.selected_cell[1]][self.selected_cell[0]]
            if not isinstance(selected_cell, Piece):
                return
            for i, line in enumerate(self.board):
                for j, cell in enumerate(line):
                    if selected_cell.can_move(j, i):
                        draw_cell_borders((j, i), AVAILABLE_MOVES_COLOR)

        def draw_history():
            """Отобразить историю ходов"""
            indent = 40

            x_first = Board.LEFT + Board.CELL_SIZE * self.width + Board.BORDER_WIDTH + 80
            x_second = x_first + 130
            y = Board.TOP - Board.BORDER_WIDTH - 30
            write_text("ИСТОРИЯ", (x_first + x_second) // 2, y, 40)
            y += 5

            count = 12 * 2
            last_records = self.history[-count:] if len(self.history) % 2 == 0 else self.history[-count + 1:]
            for i, record in enumerate(last_records):
                if i % 2 == 0:
                    x = x_first
                    y += indent
                else:
                    x = x_second
                write_text(record, x, y, 30)

        self.clean()

        screen.fill(BACKGROUND_COLOR)

        draw_borders()
        draw_scales()
        draw_cells()

        draw_move()
        draw_winner()

        self.update_pieces()
        pieces_group.draw(screen)

        draw_selected_cells_borders()

        draw_history()

        if isinstance(self.pieces_selector, PiecesSelector):
            self.pieces_selector.render(screen)

    def get_cell(self, mouse_pos):
        """Получить координаты клетки по позиции"""
        coordinates = (mouse_pos[0] - Board.LEFT) // Board.CELL_SIZE, \
                      (mouse_pos[1] - Board.TOP) // Board.CELL_SIZE
        if coordinates[0] not in range(self.width) or coordinates[1] not in range(self.height):
            return None
        return coordinates

    def get_position(self, coordinates):
        """Получить позицию по координатам клетки"""
        x = Board.LEFT + Board.CELL_SIZE * coordinates[0]
        y = Board.TOP + Board.CELL_SIZE * coordinates[1]
        return x, y

    def update_pieces(self):
        """Обновить спрайты фигур"""
        for i, line in enumerate(self.board):
            for j, cell in enumerate(line):
                if isinstance(cell, Piece):
                    size = cell.rect.size
                    cell.rect.x = Board.LEFT + Board.CELL_SIZE * (j + 0.5) - size[0] // 2
                    cell.rect.y = Board.TOP + Board.CELL_SIZE * (i + 0.5) - size[1] // 2

    def find_kings(self):
        """Найти королей"""
        kings = []
        for line in self.board:
            for cell in line:
                if isinstance(cell, King):
                    kings.append(cell)
        return kings

    def checkmate(self):
        """Проверка, поставлен ли шах"""
        # Находится ли один из королей под угрозой
        for king in self.find_kings():
            if king.is_under_attack():
                return True
        return False

    def check_winner(self):
        """Проверка, завершена ли игра"""
        def check_king(king: King):
            x1, y1 = king.get_coordinates()

            available_moves = []
            for i in range(self.width):
                for j in range(self.height):
                    if king.can_move(i, j):
                        available_moves.append((i, j))

            self.board[y1][x1] = None
            flag = True
            for x2, y2 in available_moves:
                piece = self.board[y2][x2]
                self.board[y2][x2] = king
                if not king.is_under_attack():
                    flag = False
                    break
                self.board[y2][x2] = piece

            self.board[y1][x1] = king

            return flag

        winner = None

        kings = self.find_kings()
        for king in kings:
            if check_king(king):
                winner = opponent(king.color)
                break

        if winner is not None:
            self.locked = True
        return winner

    def on_click(self, cell_coordinates):
        """Обработка выбранной фигуры"""
        def human_format(coordinates):
            x, y = coordinates
            return chr(ord('A') + y) + str(x + 1)

        x2, y2 = cell_coordinates

        # Если ранее не была выбрана фигура
        if self.selected_cell is None:
            cell = self.board[y2][x2]
            if isinstance(cell, Piece) and cell.color == self.current_color:
                self.selected_cell = cell_coordinates
            return

        # Если пользователь выбрал ту же фигуру, что и ранее
        if cell_coordinates == self.selected_cell:
            self.selected_cell = None
            return

        x1, y1 = self.selected_cell
        cell = self.board[y1][x1]
        if isinstance(cell, Piece):
            result = cell.move(x2, y2)
            # Если ход совершен успешно
            if result:
                # Добавить запись в историю
                self.history.append(human_format((x1, y1)) + ' -> ' + human_format((x2, y2)))
                # Если не существует pieces_selector, поменять цвет
                if not isinstance(self.pieces_selector, PiecesSelector):
                    self.current_color = opponent(self.current_color)
        self.selected_cell = None

    def get_click(self, mouse_pos):
        """Обработать клик"""

        # Проверка существование pieces_selector
        if isinstance(self.pieces_selector, PiecesSelector):
            piece = self.pieces_selector.get_piece(mouse_pos)
            # Проверка выбора пользователем фигуры
            if isinstance(piece, Piece):
                # Заменить фигуру
                x, y = self.changing_piece.get_coordinates()
                self.board[y][x] = piece
                self.pieces_selector = None
                self.changing_piece = None
                self.current_color = opponent(self.current_color)
            return

        # Проверка заблокировано ли поле
        if self.locked:
            return

        cell = self.get_cell(mouse_pos)
        if not cell:
            return
        self.on_click(cell)


class Piece(pygame.sprite.Sprite):
    IMAGE = ""

    def __init__(self, parent: Board, color):
        super().__init__(pieces_group, all_sprites)

        self.parent = parent
        self.color = color
        self.moved = False

        image_name = gen_piece_image_name(self.__class__.IMAGE, color)
        self.image = load_image(image_name, size=(Board.CELL_SIZE, Board.CELL_SIZE))
        self.rect = self.image.get_rect()

    def get_coordinates(self):
        """Получить координаты фигуры"""
        for i, line in enumerate(self.parent.board):
            for j, cell in enumerate(line):
                if cell == self:
                    return j, i
        return None

    def can_move(self, x, y):
        """Проверить может ли фигура пойти в клетку (x, y)"""
        if x not in range(self.parent.width) or y not in range(self.parent.height):
            return False
        cell = self.parent.board[y][x]
        if isinstance(cell, Piece) and cell.color == self.color:
            return False
        return True

    def move(self, x, y):
        """Сделать ход в клетку (x, y)"""
        if not self.can_move(x, y):
            return False
        x1, y1 = self.get_coordinates()
        self.parent.board[y][x] = self
        self.parent.board[y1][x1] = None
        self.moved = True
        return True

    def is_under_attack(self):
        """Проверить находится ли фигура под угрозой вражеских фигур"""
        x, y = self.get_coordinates()
        for line in self.parent.board:
            for cell in line:
                if isinstance(cell, Piece) and cell.color == opponent(self.color)\
                        and cell.can_move(x, y):
                    return True
        return False


class Pawn(Piece):
    """Пешка"""
    IMAGE = "pawn"

    def can_move(self, x, y):
        if not super().can_move(x, y):
            return False
        return True

    def move(self, x, y):
        if not super().move(x, y):
            return False
        if y == opponent(self.color) * 7:
            self.parent.changing_piece = self
            self.parent.pieces_selector = PiecesSelector(self.parent, self.color)
        return True


class Rook(Piece):
    """Ладья"""
    IMAGE = "rook"

    def can_move(self, x, y):
        if not super().can_move(x, y):
            return False
        return True


class Knight(Piece):
    """Конь"""
    IMAGE = "knight"

    def can_move(self, x, y):
        if not super().can_move(x, y):
            return False
        return True


class Bishop(Piece):
    """Слон"""
    IMAGE = "bishop"

    def can_move(self, x, y):
        if not super().can_move(x, y):
            return False
        return True


class Queen(Piece):
    """Ферзь"""
    IMAGE = "queen"

    def can_move(self, x, y):
        if not super().can_move(x, y):
            return False
        return True


class King(Piece):
    """Король"""
    IMAGE = "king"

    def can_move(self, x, y):
        if not super().can_move(x, y):
            return False
        return True


class PiecesSelector:
    """Выбор фигур для превращения"""
    def __init__(self, board, color):
        self.pieces = (Pawn, Rook, Knight, Bishop, Queen)

        self.board = board
        self.color = color

        indent = 30
        self.text_height = 40
        self.left = Board.LEFT + indent
        self.width = Board.CELL_SIZE * board.width - indent * 2
        self.height = self.cell_size = self.width // len(self.pieces)
        self.top = Board.TOP + Board.CELL_SIZE * (board.height / 2) - self.height / 2

    def render(self, screen):
        def write_text(string, x, y, size):
            font = pygame.font.Font(None, size)
            text = font.render(string, True, MAIN_COLOR)
            text_x = x - text.get_width() // 2
            text_y = y - text.get_height() // 2
            screen.blit(text, (text_x, text_y))

        def draw_background():
            color = BACKGROUND_COLOR
            rect = (self.left, self.top - self.text_height, self.width, self.height + self.text_height)
            pygame.draw.rect(screen, color, rect, 0)

        def draw_borders():
            color = MAIN_COLOR
            width = 1

            rect = (self.left, self.top - self.text_height, self.width, self.height + self.text_height)
            pygame.draw.rect(screen, color, rect, width)

            for i in range(len(self.pieces)):
                rect = (self.left + i * self.cell_size, self.top, self.cell_size, self.height)
                pygame.draw.rect(screen, color, rect, width)

        def draw_title():
            x = self.left + self.width // 2
            y = self.top - self.text_height // 2
            title = "Выберите фигуру"
            size = 30
            write_text(title, x, y, size)

        def draw_pieces():
            for i, piece in enumerate(self.pieces):
                image_name = gen_piece_image_name(piece.IMAGE, self.color)
                image = load_image(image_name, size=(self.cell_size, self.cell_size))
                x = self.left + i * self.cell_size
                y = self.top
                rect = image.get_rect().move(x, y)
                screen.blit(image, rect)

        draw_background()
        draw_borders()
        draw_title()
        draw_pieces()

    def get_piece(self, mouse_pos):
        """Обработать клик"""
        if not self.top <= mouse_pos[1] <= self.top + self.height:
            return None
        index = (mouse_pos[0] - self.left) // self.cell_size
        if index not in range(len(self.pieces)):
            return None
        return self.pieces[index](self.board, self.color)


SIZE = WIDTH, HEIGHT = 800, 600
CAPTION = "Шахматы"
ICON = "icon.png"
BACKGROUND_COLOR = pygame.Color(139, 69, 19)
MAIN_COLOR = pygame.Color(214, 171, 111)
SELECTED_CELL_COLOR = pygame.Color(201, 187, 52)
AVAILABLE_MOVES_COLOR = pygame.Color(69, 148, 38)

BLACK, WHITE = 0, 1

if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption(CAPTION)
    screen = pygame.display.set_mode(SIZE)

    icon = load_image(ICON)
    pygame.display.set_icon(icon)

    # start_screen()

    all_sprites = pygame.sprite.Group()
    pieces_group = pygame.sprite.Group()

    board = Board(8, 8)
    board.render(screen)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.MOUSEBUTTONDOWN:
                board.get_click(event.pos)
                board.render(screen)

        pygame.display.flip()

    pygame.quit()

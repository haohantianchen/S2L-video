from typing import Callable, Optional, Generator, List

import numpy as np


import random

# Whatever this is, it's utterly cursed.
def ordered_halving(val):
    bin_str = f"{val:064b}"
    bin_flip = bin_str[::-1]
    as_int = int(bin_flip, 2)

    return as_int / (1 << 64)


# I have absolutely no idea how this works and I don't like that.
def uniform(
    step: int = ...,
    num_steps: Optional[int] = None,
    num_frames: int = ...,
    context_size: Optional[int] = None,
    context_stride: int = 3,
    context_overlap: int = 4,
    closed_loop: bool = True,
):
    if num_frames <= context_size:
        yield list(range(num_frames))
        return

    context_stride = min(context_stride, int(np.ceil(np.log2(num_frames / context_size))) + 1)

    for context_step in 1 << np.arange(context_stride):
        # pad = int(round(num_frames * ordered_halving(step)))
        pad = 0
        for j in range(
            int(ordered_halving(step) * context_step) + pad,
            num_frames + pad + (0 if closed_loop else -context_overlap),
            (context_size * context_step - context_overlap),
        ):
            yield [e % num_frames for e in range(j, j + context_size * context_step, context_step)]


def shuffle(
    step: int = ...,
    num_steps: Optional[int] = None,
    num_frames: int = ...,
    context_size: Optional[int] = None,
    context_stride: int = 3,
    context_overlap: int = 4,
    closed_loop: bool = True,
):
    import random
    c = list(range(num_frames))
    c = random.sample(c, len(c))

    if len(c) % context_size:
        c += c[0:context_size - len(c) % context_size]

    c = random.sample(c, len(c))

    for i in range(0, len(c), context_size):
        yield c[i:i+context_size]


def composite(
    step: int = ...,
    num_steps: Optional[int] = None,
    num_frames: int = ...,
    context_size: Optional[int] = None,
    context_stride: int = 3,
    context_overlap: int = 4,
    closed_loop: bool = True,
):
    if (step/num_steps) < 0.1:
        return shuffle(step,num_steps,num_frames,context_size,context_stride,context_overlap,closed_loop)
    else:
        return uniform(step,num_steps,num_frames,context_size,context_stride,context_overlap,closed_loop)


# def my_she(
#     step: int = ...,
#     num_steps: Optional[int] = None,
#     num_frames: int = ...,
#     context_size: Optional[int] = None,
#     context_stride: int = 3,
#     context_overlap: int = 4,
#     closed_loop: bool = True,
# ):
#     # my_overlap = random.randint(9, 15)
#     my_overlap = 15
#     if num_frames <= context_size:
#         yield list(range(num_frames))
#         return

#     context_stride = min(context_stride, int(np.ceil(np.log2(num_frames / context_size))) + 1)

#     for context_step in 1 << np.arange(context_stride):
#         # pad = int(round(num_frames * ordered_halving(step)))
#         pad = 0
#         for j in range(
#             int(ordered_halving(step) * context_step) + pad,
#             num_frames + pad + (0 if closed_loop else - my_overlap),
#             (context_size * context_step - my_overlap),
#         ):
#             # yield [e % num_frames for e in range(j, j + context_size * context_step, context_step)]
#             yield [[e % num_frames for e in range(j, j + context_size * context_step, context_step)], my_overlap]




# 创建一个生成器函数来在调用时循环my_overlap的值，从8开始
def my_shift_generator():
    value = 6
    while True:
        yield value
        value = value + 1 if value < 7 else 0  # 循环回0

# 创建my_shift生成器实例
my_shift_gen = my_shift_generator()

def my_she(
    step: int = ...,
    num_steps: Optional[int] = None,
    num_frames: int = ...,
    context_size: Optional[int] = None,
    context_stride: int = 3,
    context_overlap: int = 4,
    closed_loop: bool = True,
):

    if num_frames <= context_size:
        yield list(range(num_frames))
        return

    context_stride = min(context_stride, int(np.ceil(np.log2(num_frames / context_size))) + 1)

    for context_step in 1 << np.arange(context_stride):
        my_shift = next(my_shift_gen)

        # pad = int(round(num_frames * ordered_halving(step)))
        pad = 0
        yield [[e % num_frames for e in range(0, context_size * context_step, context_step)], context_overlap + my_shift]
        for j in range(
            # int(ordered_halving(step) * context_step) + pad,
            context_size * context_step - context_overlap - my_shift,
            num_frames + pad + (0 if closed_loop else - context_overlap),
            (context_size * context_step - context_overlap),
        ):
            # yield [e % num_frames for e in range(j, j + context_size * context_step, context_step)]
            yield [[e % num_frames for e in range(j, j + context_size * context_step, context_step)], context_overlap]


def get_context_scheduler(name: str) -> Callable:
    match name:
        case "uniform":
            return uniform
        case "shuffle":
            return shuffle
        case "composite":
            return composite
        case "my_she":
            return my_she
        case _:
            raise ValueError(f"Unknown context_overlap policy {name}")


def get_total_steps(
    scheduler,
    timesteps: list[int],
    num_steps: Optional[int] = None,
    num_frames: int = ...,
    context_size: Optional[int] = None,
    context_stride: int = 3,
    context_overlap: int = 4,
    closed_loop: bool = True,
):
    return sum(
        len(
            list(
                scheduler(
                    i,
                    num_steps,
                    num_frames,
                    context_size,
                    context_stride,
                    context_overlap,
                )
            )
        )
        for i in range(len(timesteps))
    )
